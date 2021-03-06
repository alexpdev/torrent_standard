import re
import os


class BencodeDecoder:

    def __init__(self, text=None):
        self.raw = text if text else None
        self.decoded = {}

    def decode_all(self, bits):
        self.text = bits
        dic, feed = self.decode(bits)
        return dic

    def decode(self, bits):
        if bits.startswith(b"i"):
            match, feed = self.de_int(bits)
            return match, feed
        elif chr(bits[0]).isdigit():
            match, feed = self.de_str(bits)
            return match, feed
        elif bits.startswith(b"l"):
            lst, feed = self.de_list(bits)
            return lst, feed
        elif bits.startswith(b"d"):
            dic, feed = self.de_dict(bits)
            return dic, feed
        else:
            raise Exception

    def de_dict(self, bits):
        dic, feed = {}, 1
        while not bits[feed:].startswith(b"e"):
            match1, rest = self.decode(bits[feed:])
            feed += rest
            match2, rest = self.decode(bits[feed:])
            feed += rest
            dic[match1] = match2
        feed += 1
        return dic, feed

    def de_list(self, bits):
        lst, feed = [], 1
        while not bits[feed:].startswith(b"e"):
            match, rest = self.decode(bits[feed:])
            lst.append(match)
            feed += rest
        feed += 1
        return lst, feed

    def de_str(self, bits):
        match = re.match(b"(\\d+):", bits)
        word_len, start = int(match.groups()[0]), match.span()[1]
        word = bits[start: start + word_len]
        try:
            word = word.decode("utf-8")
        except:
            word = word
        return word, start + word_len

    def de_int(self, bits):
        obj = re.match(b"i(-?\d+)e", bits)
        return int(obj.group(1)), obj.end()


class BencodeEncoder:

    def __init__(self, data=None):
        self.info = data

    def encode_all(self):
        output = self.encode(self.info)
        return output

    def encode(self, val):
        if type(val) == str:
            return self.to_str(val)
        elif type(val) == int:
            return self.to_int(val)
        elif type(val) == list:
            return self.to_list(val)
        elif type(val) == dict:
            return self.to_dict(val)
        else:
            return

    def to_str(self, txt):
        size = str(len(txt)).encode("utf-8")
        return size + b":" + txt.encode("utf-8")

    def to_int(self, i):
        return b"i" + b"{i}" + b"e"

    def to_list(self, elems):
        lst = [b"l"]
        for elem in elems:
            encoded = self.encode(elem)
            lst.append(encoded)
        lst.append(b"e")
        bit_lst = b"".join(lst)
        return bit_lst

    def to_dict(self, dic):
        result = b"d"
        for k, v in dic.items():
            result += b"".join([self.encode(k), self.encode(v)])
        return result + b"e"


class Torrent:

    def __init__(self):
        self.encoder = BencodeEncoder()
        self.decoder = BencodeDecoder()
        self.meta = {}

    def __str__(self):
        if self.name:
            return "Torrent: " + self.name
        else:
            return "Torrent:(empty)"

    def read(self, torrent):
        if not isinstance(torrent, bytes):
            print(type(torrent))
            torrent = os.open(torrent, "rb")
        meta = self.decoder.decode_all(torrent)
        self.organize_metadata(meta)
        return self

    def translate(self, contents):
        meta = self.decoder.decode_all(contents)
        self.organize_metadata(meta)

    def organize_metadata(self, meta):
        # print(meta.keys())
        info = meta["info"]
        for k, v in meta.items():
            if k not in ["pieces", "info", "piece_length"]:
                self.meta[k] = v
        self.contents = []
        for k, v in info.items():
            if k == "path":
                self.contents.append(v)
            elif k not in ["pieces","piece_length"]:
                self.meta[k] = v

    @classmethod
    def create(self, data):
        info = BencodeEncoder(data)
        self.meta = info.encode_all()

    def info(self):
        print(self.name, self.contents, self.info)
