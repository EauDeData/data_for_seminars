import spotipy
import spotipy.oauth2 as oauth2
import pickle
import time
import networkx as nx

LIMIT = 50
ITERATIONS = 1000000

class Crawler:
    def __init__(self, key = None, skey = None):
        self.my_client =  key
        self.secret_client =  skey
        self.api = self.set_spotify() #Uses previous keys parameters for authorization
        self.graf = {} #The representation is a dictionary | KEY: [[ARTIST, #COLABOS] ... ]
        return None

    def set_spotify(self):

        '''

        Returns an spotipy.spotify object with the required autentification tocken

        '''

        token = oauth2.SpotifyClientCredentials(client_id=self.my_client, client_secret=self.secret_client)
        #print(token)
        cache_token = token.get_access_token()['access_token']
        spotify = spotipy.Spotify(cache_token)
        #print(spotify.search())


        return spotify
    
    def get_artist(self, name):
        search = self.api.search(name, type= 'artist')['id']['items']
        return search[0]
    
    def albums_by_artist(self, id_art):
        results1 = self.api.artist_albums(id_art, album_type='album', limit = LIMIT)['items']
        results2 = self.api.artist_albums(id_art, album_type='single', limit = LIMIT)['items']
        results3 = self.api.artist_albums(id_art, album_type='compilation', limit = LIMIT)['items']
        return results1 + results2 + results3
    def get_connected(self, name):
        tracks = self.discography(name)
        relations = []
        for track in tracks:
            artists = track['artists']
            for artist in artists:
                if artist['id']!= name:
                    relations.append(artist['id'])
        return relations

    def process_relations(self, rel):
        rel = {i: rel.count(i) for i in rel}
        rel = [[i, rel[i]] for i in rel]
        return rel

    def discography(self, name):
        
        albums = self.albums_by_artist(name)
        tracks = []
        for album in albums:
             results = self.api.album_tracks(album['id'], limit = 50)['items']
             for track in results:
                 tracks.append(track)
        return tracks
    def to_pickle(self):
        self.format()
        pickle.dump(self.readable, open('graf.p', 'wb'))
    def id2name(self, id):
        return self.api.artist(id)['name']

    def to_graf(self, filename):
        graf = pickle.load(open(filename, 'rb'))
        G = nx.Graph(is_directed = False)
        acc = []
        for lists in graf.values():
            for usr in lists:
                if not usr[0] in acc:
                    acc.append(usr[0])
        for key in graf:
            for node in graf[key]:
                G.add_edge(key, node[0], weight = 1/node[1])
        return G

    def to_gephi(self, g):
        nx.write_gexf(g, './graph.gexf')
        return None

    def add_arestes(self, art1, rela):
        self.graf[art1] = rela
    def format(self):
        self.readable = {}
        for key in self.graf:
            total = []
            for pair in self.graf[key]:
                total.append([self.id2name(pair[0]), pair[1]])
            self.readable[self.id2name(key)] = total
    def save_state(self, q, i):
        pickle.dump([q, i], open('scheduler_sv.p', 'wb'))
        return None
    def scheduler(self, seed_node, save_state = True):
        try:
            savestate = pickle.load(open('scheduler_sv.p', 'rb'))
            if not save_state:
                raise FileNotFoundError
            queue = savestate[0]
            index = savestate[1]
        except FileNotFoundError:           
            queue = [self.api.search(node, type= 'artist')['artists']['items'][0]['id'] for node in seed_node]
            index = 0
        while index < ITERATIONS:
            try:
                try:
                    conn = self.process_relations(self.get_connected(queue[index]))
                    queue += [i[0] for i in conn if not i[0] in queue]  #DFS
                    self.add_arestes(queue[index], conn)
                except IndexError:
                    print(queue[index], 'no té colabos.')
                    index += 1
                if save_state:
                    self.save_state(queue, index)
                
                self.to_pickle()
                self.to_gephi(self.to_graf('graf.p'))
                if index%2 == 0:
                    print('Iteration {}/1000'.format(index))
                    del self.api
                    self.api = self.set_spotify()
                    self.format()
                    print(list(self.readable.keys())[-1]+':',self.readable[list(self.readable.keys())[-1]])
                index += 1
            except:
                print('Connection closed, sleeping 900sec.')
                time.sleep(900)
                self.api = self.set_spotify()
    
if __name__ == '__main__':
    key = "141b13d2b2294afcae74ee73b97e6fee" #input('Please, enter your API key: ')
    skey = "27b4bdcccc5e41e6b31a865d5c394e66" #input('Please, now enter your secret API key: ')
    ob = Crawler(key=key, skey=skey)
    ob.scheduler([input('Enter your starting artist (seed node): ')])
    
