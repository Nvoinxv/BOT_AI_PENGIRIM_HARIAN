import logging
from datetime import datetime
import hashlib
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from src.config.settings import MONGO_URL, MONGO_DB_NAME

logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Layanan koneksi MongoDB terpusat untuk Beatrice Daily Bot.
    Menggunakan rute koneksi yang sama dengan EDU_BOT (satu VPS / jaringan Docker 'shared_mongo_net').
    Bertujuan untuk menyimpan riwayat briefing dan percakapan guna memperkecil pengulangan respon AI.
    """
    _instance = None
    _client = None
    _db = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseService, cls).__new__(cls)
            cls._instance._connect()
        return cls._instance

    def _connect(self):
        # Daftar rute percobaan koneksi (memprioritaskan rute EDU_BOT mongodb:27017 dan fallback lokal host)
        urls_to_try = [
            MONGO_URL,
            "mongodb://mongodb:27017",
            "mongodb://localhost:27017",
            "mongodb://127.0.0.1:27017"
        ]
        seen = set()
        for url in urls_to_try:
            if not url or url in seen:
                continue
            seen.add(url)
            try:
                client = MongoClient(url, serverSelectionTimeoutMS=2500)
                # Uji ping koneksi
                client.admin.command('ping')
                self._client = client
                self._db = client[MONGO_DB_NAME]
                logger.info(f"✅ Sukses terhubung ke MongoDB via route: {url} (Database: {MONGO_DB_NAME})")
                self._setup_indexes()
                return
            except Exception as e:
                logger.debug(f"Percobaan koneksi MongoDB ke {url} gagal: {e}")
        
        logger.warning("⚠️ Tidak dapat terhubung ke MongoDB lokal/VPS. Fitur memori persistent dinonaktifkan sementara.")

    def _setup_indexes(self):
        if self._db is None:
            return
        try:
            briefings = self._db["generated_briefings"]
            briefings.create_index([("text_hash", 1)], unique=True, background=True)
            briefings.create_index([("generated_at", -1)], background=True)

            chat = self._db["chat_history"]
            chat.create_index([("timestamp", 1)], background=True)
            logger.info("✅ Index MongoDB untuk koleksi memori & chat berhasil dibuat/diperiksa.")
        except Exception as e:
            logger.warning(f"Gagal mengatur index MongoDB: {e}")

    def is_connected(self) -> bool:
        return self._db is not None

    def check_if_similar_exists(self, new_text: str, briefing_type: str = "macro", similarity_threshold: float = 0.72) -> bool:
        """
        Memeriksa apakah konten baru terlalu mirip dengan briefing sebelumnya di database
        menggunakan metode Jaccard Word Similarity (algoritma selaras dengan EDU_BOT).
        """
        if self._db is None or not new_text:
            return False
        try:
            collection = self._db["generated_briefings"]
            recent_docs = list(collection.find(
                {"type": briefing_type},
                {"text": 1}
            ).sort("generated_at", -1).limit(10))

            if not recent_docs:
                return False

            new_words = set(new_text.lower().split())
            if not new_words:
                return False

            for doc in recent_docs:
                old_words = set(doc.get("text", "").lower().split())
                if not old_words:
                    continue

                intersection = new_words.intersection(old_words)
                union = new_words.union(old_words)
                if not union:
                    continue
                similarity = len(intersection) / len(union)

                if similarity > similarity_threshold:
                    logger.warning(f"⚠️ Konten terlalu mirip dengan riwayat sebelumnya (similarity: {similarity:.2f})")
                    return True

            return False
        except Exception as e:
            logger.warning(f"Error saat pengecekan kemiripan konten di MongoDB: {e}")
            return False

    def save_briefing(self, text: str, briefing_type: str = "macro") -> bool:
        """
        Menyimpan hasil briefing ke MongoDB agar AI memiliki ingatan jangka panjang.
        """
        if self._db is None or not text:
            return False
        try:
            collection = self._db["generated_briefings"]
            text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()

            doc = {
                "text": text,
                "text_hash": text_hash,
                "type": briefing_type,
                "generated_at": datetime.now()
            }
            collection.insert_one(doc)
            logger.info(f"✅ Briefing ({briefing_type}) berhasil disimpan ke memori MongoDB.")
            return True
        except DuplicateKeyError:
            logger.warning("⚠️ Briefing duplikat terdeteksi (hash sama), dilewati.")
            return False
        except Exception as e:
            logger.warning(f"Gagal menyimpan briefing ke MongoDB: {e}")
            return False

    def get_recent_briefings_context(self, briefing_type: str = "macro", limit: int = 1) -> str:
        """
        Mengambil ringkasan briefing sebelumnya untuk disuntikkan ke prompt Gemini
        supaya Gemini tidak mengulang bahasan yang persis sama.
        """
        if self._db is None:
            return ""
        try:
            collection = self._db["generated_briefings"]
            recent_docs = list(collection.find(
                {"type": briefing_type},
                {"text": 1, "generated_at": 1}
            ).sort("generated_at", -1).limit(limit))

            if not recent_docs:
                return ""

            summaries = []
            for doc in recent_docs:
                text_preview = doc.get("text", "")[:400].replace("\n", " ")
                summaries.append(f"- [{doc.get('generated_at')}] {text_preview}...")

            return "\n".join(summaries)
        except Exception as e:
            logger.warning(f"Gagal mengambil riwayat briefing dari MongoDB: {e}")
            return ""

    def save_chat_message(self, role: str, content: str):
        """
        Menyimpan pesan percakapan DM Discord (user/model) ke MongoDB.
        """
        if self._db is None or not content:
            return
        try:
            collection = self._db["chat_history"]
            collection.insert_one({
                "role": role,
                "content": content,
                "timestamp": datetime.now()
            })
        except Exception as e:
            logger.warning(f"Gagal menyimpan pesan chat ke MongoDB: {e}")

    def get_chat_history(self, limit: int = 16) -> list:
        """
        Mengambil riwayat percakapan DM terakhir untuk di-load ke sesi chat Gemini.
        """
        if self._db is None:
            return []
        try:
            collection = self._db["chat_history"]
            docs = list(collection.find({}, {"role": 1, "content": 1}).sort("timestamp", -1).limit(limit))
            # Balik urutan dari lama ke baru
            docs.reverse()

            history = []
            for d in docs:
                role = d.get("role", "user")
                # Pastikan role valid untuk Gemini (user atau model)
                if role not in ["user", "model"]:
                    role = "user"
                history.append({"role": role, "parts": [d.get("content", "")]})
            return history
        except Exception as e:
            logger.warning(f"Gagal mengambil riwayat chat dari MongoDB: {e}")
            return []

def get_db() -> DatabaseService:
    return DatabaseService()
