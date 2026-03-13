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
        final = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=3000,
            messages=[{
                "role": "user",
                "content": (
                    f"List EXACTLY 10 tourist attractions in {location}, no more, no less. "
                    "You MUST return ONLY a valid JSON object, no markdown, no explanation. "
                    "Each attraction MUST have a 'description' field with exactly 2 full sentences about the attraction. "
                    "Use this exact format:\n"
                    '{"attractions": ['
                    '{"rank": 1, "name": "Eiffel Tower", "description": "The Eiffel Tower is a world-famous iron lattice tower standing 330 meters tall in the heart of Paris. Built in 1889, it attracts millions of visitors each year and offers stunning views of the city."}'
                    ', ...]}'
                )
            }]
        )

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
