import sqlite3
from flask import Flask, jsonify
from flask_restful import Resource, Api, reqparse
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)
api = Api(app)

SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.json'

swagger_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Music Library API"
    }
)

app.register_blueprint(swagger_blueprint, url_prefix=SWAGGER_URL)

# Подключаемся к db
conn = sqlite3.connect('music.db', check_same_thread=False)
c = conn.cursor()

# Создаём таблицы

c.execute('''CREATE TABLE IF NOT EXISTS songs
             (id INTEGER PRIMARY KEY, title TEXT, artist TEXT, genre TEXT, duration INTEGER, album TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS playlists
             (id INTEGER PRIMARY KEY, name TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS playlist_songs
             (playlist_id INTEGER, song_id INTEGER, FOREIGN KEY(playlist_id) REFERENCES playlists(id), FOREIGN KEY(song_id) REFERENCES songs(id))''')
c.execute('''CREATE TABLE IF NOT EXISTS song_ratings
             (song_id INTEGER, rating INTEGER, FOREIGN KEY(song_id) REFERENCES songs(id))''')

# Чтобы что-то было изначально для примера
c.execute("INSERT INTO songs (title, artist, genre, duration, album) VALUES ('Mein Herz brennt', 'Rammstein', 'Rock', 180, 'Mutter')")
c.execute("INSERT INTO songs (title, artist, genre, duration, album) VALUES ('Imagine Dragons', 'Enemy', 'Pop', 240, 'Mercury - Act 1')")
c.execute("INSERT INTO playlists (name) VALUES ('Playlist 1')")
c.execute("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (1, 1)")

conn.commit()

# Парсилки
song_parser = reqparse.RequestParser()
song_parser.add_argument('title', type=str, required=True, location='json')
song_parser.add_argument('artist', type=str, required=True, location='json')
song_parser.add_argument('genre', type=str, required=True, location='json')
song_parser.add_argument('duration', type=int, required=True, location='json')
song_parser.add_argument('album', type=str, required=True, location='json')

playlist_parser = reqparse.RequestParser()
playlist_parser.add_argument('name', type=str, required=True, location='json')

song_id_parser = reqparse.RequestParser()
song_id_parser.add_argument('song_id', type=int, required=True, location='json')

rating_parser = reqparse.RequestParser()
rating_parser.add_argument('song_id', type=int, required=True, location='json')
rating_parser.add_argument('rating', type=int, required=True, location='json')


class SongList(Resource):
    def get(self):
        c.execute("SELECT title, artist, genre FROM songs")
        songs = c.fetchall()
        print(songs)
        return jsonify(songs)

    def post(self):
        args = song_parser.parse_args()
        c.execute("INSERT INTO songs (title, artist, genre, duration, album) VALUES (?, ?, ?, ?, ?)", (args['title'], args['artist'], args['genre'], args['duration'], args['album']))
        conn.commit()
        return jsonify({'success': True})

class Song(Resource):
    def get(self, id):
        c.execute("SELECT title, artist, genre, duration, album FROM songs WHERE id=?", (id,))
        song = c.fetchone()
        if song:
            return jsonify(song)
        else:
            return jsonify({'error': 'Song not found'})

class Playlist(Resource):
    def post(self):
        args = playlist_parser.parse_args()
        c.execute("INSERT INTO playlists (name) VALUES (?)", (args['name'],))
        conn.commit()
        return jsonify({'success': True})

class PlaylistSong(Resource):
    def post(self, id):
        args = song_id_parser.parse_args()
        c.execute("INSERT INTO playlist_songs (playlist_id, song_id) VALUES (?, ?)", (id, args['song_id']))
        conn.commit()
        return jsonify({'success': True})

class SongRating(Resource):
    def post(self):
        args = rating_parser.parse_args()
        c.execute("INSERT INTO song_ratings (song_id, rating) VALUES (?, ?)", (args['song_id'], args['rating']))
        conn.commit()
        return jsonify({'success': True})

api.add_resource(SongList, '/songs')
api.add_resource(Song, '/songs/<int:id>')
api.add_resource(Playlist, '/playlists')
api.add_resource(PlaylistSong, '/playlists/<int:id>/songs')
api.add_resource(SongRating, '/ratings')

if __name__ == '__main__':
    app.run(debug=True)
