from flask import Flask, request, jsonify, send_from_directory
import anthropic
import json
import os

app = Flask(__name__, static_folder='.')
client = anthropic.Anthropic()


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/api/attractions', methods=['POST'])
def get_attractions():
    data = request.get_json()
    location = data.get('location', '').strip()

    if not location:
        return jsonify({'error': 'Location is required'}), 400

    try:
        with client.messages.stream(
            model="claude-sonnet-4-20250514",
            max_tokens=2500,
            messages=[{
                "role": "user",
                "content": (
                    f"List the top 10 tourist attractions in {location}. "
                    "Return ONLY valid JSON (no markdown code blocks, no explanation text) "
                    "in exactly this format:\n"
                    '{"attractions": [{"rank": 1, "name": "Attraction Name", '
                    '"paragraph1": "First detailed paragraph...", '
                    '"paragraph2": "Second detailed paragraph..."}, ...]}\n'
                    "Include exactly 10 attractions ranked by importance. "
                    "Each paragraph should be 3-4 rich, informative sentences covering history, "
                    "what to expect, and why it is worth visiting."
                )
            }]
        ) as stream:
            final = stream.get_final_message()

        text_blocks = [b.text for b in final.content if b.type == "text"]
        if not text_blocks:
            return jsonify({'error': 'No text response from AI'}), 500

        text = text_blocks[-1].strip()

        # Strip markdown code fences if present
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            text = text.split("```")[1].split("```")[0].strip()

        result = json.loads(text)
        return jsonify(result)

    except json.JSONDecodeError as e:
        return jsonify({'error': f'Failed to parse AI response: {str(e)}'}), 500
    except anthropic.APIError as e:
        return jsonify({'error': f'API error: {str(e)}'}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, port=port)
