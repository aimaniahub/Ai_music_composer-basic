from flask import Flask, request, jsonify, render_template, send_from_directory
import numpy as np
import pretty_midi
from keras.models import load_model
from midi2audio import FluidSynth
from pydub import AudioSegment
import os
import random

app = Flask(__name__)

# Load your music model and soundfont
model = load_model('backend/trained_music_model.h5')

soundfont_path = 'C:\\ProgramData\\soundfonts\\FluidR3_GM.sf2'

output_directory = '/new_files'
os.makedirs(output_directory, exist_ok=True)
file_counter = 0

# Updated instruments and their characteristics for each genre
instruments = {
    'cinematic': [
        {'name': 'strings', 'program': 48, 'note_range': (48, 72)},
        {'name': 'brass', 'program': 57, 'note_range': (53, 77)},
        {'name': 'piano', 'program': 1, 'note_range': (36, 84)},
        {'name': 'choir', 'program': 52, 'note_range': (60, 72)},
        {'name': 'timpani', 'program': 47, 'note_range': (36, 48)},
    ],
    'melody': [
        {'name': 'piano', 'program': 1, 'note_range': (60, 84)},
        {'name': 'strings', 'program': 48, 'note_range': (55, 79)},
        {'name': 'flute', 'program': 73, 'note_range': (72, 96)},
        {'name': 'harp', 'program': 46, 'note_range': (48, 83)},
        {'name': 'celesta', 'program': 8, 'note_range': (60, 96)},
    ],
    'hiphop': [
        {'name': 'bass', 'program': 36, 'note_range': (36, 48)},
        {'name': 'synth_lead', 'program': 81, 'note_range': (48, 72)},
        {'name': 'electric_piano', 'program': 4, 'note_range': (60, 84)},
        {'name': 'percussion', 'program': 118, 'note_range': (35, 50)},
        {'name': 'scratch', 'program': 119, 'note_range': (30, 40)},
    ],
    'classical': [
        {'name': 'piano', 'program': 1, 'note_range': (40, 88)},
        {'name': 'violin', 'program': 41, 'note_range': (55, 84)},
        {'name': 'cello', 'program': 43, 'note_range': (36, 60)},
        {'name': 'flute', 'program': 73, 'note_range': (60, 96)},
        {'name': 'clarinet', 'program': 71, 'note_range': (48, 80)},
    ]
}

# Tempo mapping for genres
tempo_mapping = {
    'cinematic': 120,
    'hiphop': 100,
    'melody': 110,
    'classical': 90
}

def generate_rhythm_pattern(genre, length=16):
    base_pattern = [1, 0, 1, 0] * 4  # Example base pattern
    if genre == 'hiphop':
        return [1 if random.random() < 0.8 and base_pattern[i] else 0 for i in range(length)]
    else:
        return [1 if random.random() < 0.6 else 0 for _ in range(length)]

def get_chord_notes(root_note, chord_type='major'):
    if chord_type == 'major':
        return [root_note, root_note + 4, root_note + 7]
    elif chord_type == 'minor':
        return [root_note, root_note + 3, root_note + 7]

def generate_music(num_bars=8, notes_per_bar=16, genre='cinematic'):
    current_tempo = tempo_mapping.get(genre, 120)
    generated_notes = {instr['name']: [] for instr in instruments[genre]}
    rhythm_pattern = generate_rhythm_pattern(genre, notes_per_bar)

    chord_roots = [random.choice([60, 62, 65, 67]) for _ in range(4)]
    chord_progression = [get_chord_notes(root, random.choice(['major', 'minor'])) for root in chord_roots]

    for bar in range(num_bars):
        for instr in instruments[genre]:
            if instr['name'] in ['bass', 'piano']:
                for step in range(notes_per_bar):
                    note = random.choice(chord_progression[bar % len(chord_progression)])
                    generated_notes[instr['name']].append(note if rhythm_pattern[step] else -1)

    return generated_notes, current_tempo


def save_to_midi(generated_notes, tempo, genre):
    global file_counter
    midi_data = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    for instr in instruments[genre]:
        instrument = pretty_midi.Instrument(program=instr['program'])
        start_time = 0
        note_duration = 60 / tempo
        for note in generated_notes[instr['name']]:
            if note != -1:
                velocity = np.random.randint(70, 100)
                midi_note = pretty_midi.Note(
                    velocity=velocity, pitch=note, start=start_time, end=start_time + note_duration)
                instrument.notes.append(midi_note)
            start_time += note_duration
        midi_data.instruments.append(instrument)

    midi_filename = f"{genre}_music_{file_counter}.midi"
    midi_filepath = os.path.join(output_directory, midi_filename)
    midi_data.write(midi_filepath)
    file_counter += 1
    return midi_filepath

def midi_to_wav(midi_filepath):
    wav_filename = midi_filepath.replace('.midi', '.wav')
    wav_filepath = os.path.join(output_directory, wav_filename)
    fs = FluidSynth(soundfont_path)
    fs.midi_to_audio(midi_filepath, wav_filepath)
    return wav_filepath

def wav_to_mp3(wav_filepath):
    mp3_filename = wav_filepath.replace('.wav', '.mp3')
    mp3_filepath = os.path.join(output_directory, mp3_filename)
    sound = AudioSegment.from_wav(wav_filepath)
    sound.export(mp3_filepath, format='mp3')
    return mp3_filepath

@app.route('/')
def index():
    available_genres = list(instruments.keys())
    return render_template('index.html', genres=available_genres)

@app.route('/generate_music', methods=['POST'])
def generate_music_endpoint():
    try:
        data = request.get_json()
        genre = data.get('genre', 'cinematic')

        # Set default values for num_bars and notes_per_bar
        num_bars = 8  # Default number of bars
        notes_per_bar = 16  # Default number of notes per bar

        generated_notes, tempo = generate_music(num_bars, notes_per_bar, genre)
        midi_filepath = save_to_midi(generated_notes, tempo, genre)
        wav_filepath = midi_to_wav(midi_filepath)
        mp3_filepath = wav_to_mp3(wav_filepath)

        mp3_filename = os.path.basename(mp3_filepath)
        return jsonify({'mp3_filename': mp3_filename})

    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(output_directory, filename)

if __name__ == '__main__':
    app.run(debug=True)
