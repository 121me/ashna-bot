import os
from datetime import datetime
import sqlite3
from typing import Any

date_time_format = "%Y.%m.%d.%H.%M.%S"
user_attr = [
	"id",
	"name",
	"age",
	"university",
	"gender",
	"bio",
	"email_address",
	"so",
	"lang",
	"profile_step",
	"last_saved_media_name",
	"media_type",
	"is_profile_complete",
	"verify_code",
	"co",
	"last_online"]


def datetime_now() -> str:
	return datetime.now().strftime(date_time_format)


class UsersDB:
	def __init__(self, dbname="../static/db/users.db") -> None:
		self.dbname = dbname
		try:
			self.con = sqlite3.connect(dbname, check_same_thread=False)
		except sqlite3.OperationalError:
			# create a folder "static/db"
			os.makedirs("../static/db", exist_ok=True)
			self.con = sqlite3.connect(dbname, check_same_thread=False)
		self.cur = self.con.cursor()
		self.setup()

	def setup(self) -> None:
		stmt = """
		CREATE TABLE IF NOT EXISTS users(
			id INTEGER,
			name TEXT,
			age VARCHAR(10),
			university TEXT,
			gender VARCHAR(1),
			bio TEXT,
			email_address TEXT,
			so VARCHAR(1),
			lang VARCHAR(2),
			profile_step INTEGER,
			last_saved_media_name INTEGER,
			media_type VARCHAR(3),
			is_profile_complete INTEGER,
			verify_code VARCHAR(16),
			co INTEGER,
			last_online TEXT
		);
		CREATE TABLE IF NOT EXISTS pending_matches (
			user1 INTEGER,
			user2 INTEGER,
			date TEXT
		);
		CREATE TABLE IF NOT EXISTS matches (
			user1 INTEGER,
			user2 INTEGER,
			liked INTEGER,
			date TEXT
		);
		CREATE TABLE IF NOT EXISTS complaints (
			user1 INTEGER,
			user2 INTEGER,
			complaint INTEGER,
			date TEXT
		);
		CREATE TABLE IF NOT EXISTS errors (
			user_id INTEGER,
			error TEXT,
			date TEXT
		);"""
		self.cur.executescript(stmt)
		self.con.commit()

	# users functions
	def add_initial(self, user_id: int) -> None:
		stmt = "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"
		args = (
			user_id,
			'',
			'',
			'',
			'',
			'',
			'',
			'b',
			'',
			0,
			0,
			'',
			0,
			'',
			6,
			datetime_now())
		self.cur.execute(stmt, args)
		self.con.commit()

	def check_user(self, user_id: int) -> bool:
		stmt = "SELECT EXISTS(SELECT 1 from users WHERE id = ?);"
		args = (user_id,)
		self.cur.execute(stmt, args)
		return self.cur.fetchone() == (1,)

	def set_lang(self, user_id: int, lang: str) -> None:
		stmt = "UPDATE users SET lang = ?, profile_step = 1 WHERE id = ?;"
		args = (lang, user_id)
		self.cur.execute(stmt, args)
		self.con.commit()

	def add_name(self, user_id: int, user_name: str) -> None:
		stmt = "UPDATE users SET name = ?, profile_step = 2 WHERE id = ?;"
		args = (user_name, user_id)
		self.cur.execute(stmt, args)
		self.con.commit()

	def add_age(self, user_id: int, age: str) -> None:
		stmt = "UPDATE users SET age = ?, profile_step = 3 WHERE id = ?;"
		args = (age, user_id)
		self.cur.execute(stmt, args)
		self.con.commit()

	def add_university(self, user_id: int, university: str) -> None:
		stmt = "UPDATE users SET university = ? WHERE id = ?;"
		args = (university, user_id)
		self.cur.execute(stmt, args)
		self.con.commit()

	def add_gender(self, user_id: int, gender: str) -> None:
		stmt = "UPDATE users SET gender = ?, profile_step = 4 WHERE id = ?;"
		args = (gender, user_id)
		self.cur.execute(stmt, args)
		self.con.commit()

	def add_bio(self, user_id: int, bio: str) -> None:
		stmt = "UPDATE users SET bio = ?, profile_step = 5 WHERE id = ?;"
		args = (bio, user_id)
		self.cur.execute(stmt, args)
		self.con.commit()

	def add_media(self, user_id: int, media_type: str) -> None:
		stmt = "UPDATE users SET last_saved_media_name = last_saved_media_name + 1, profile_step = 6, media_type = ? " \
			   "WHERE id = ?; "
		args = (media_type, user_id)
		self.cur.execute(stmt, args)
		self.con.commit()

	def add_email_address(self, user_id: int, email_address: str) -> None:
		stmt = "UPDATE users SET email_address = ?, profile_step = 7 WHERE id = ?;"
		args = (email_address, user_id)
		self.cur.execute(stmt, args)
		self.con.commit()

	def check_email_address(self, email_address: str) -> bool:
		stmt = "SELECT EXISTS(SELECT 1 FROM users WHERE email_address = ? AND is_profile_complete = 1);"
		args = (email_address,)
		self.cur.execute(stmt, args)
		return self.cur.fetchone() == (1,)

	def add_so(self, user_id: int, so: str) -> None:
		stmt = "UPDATE users SET so = ? WHERE id = ?;"
		args = (so, user_id)
		self.cur.execute(stmt, args)
		self.con.commit()

	def check_verify_code(self, user_id: int, code: str) -> bool:
		stmt = "SELECT EXISTS(SELECT 1 FROM users WHERE id = ? AND verify_code = ?);"
		args = (user_id, code)
		self.cur.execute(stmt, args)
		return self.cur.fetchone() == (1,)

	def add_verify_code(self, user_id: int, code: str) -> None:
		stmt = "UPDATE users SET verify_code = ?, profile_step = 8 WHERE id = ?;"
		args = (code, user_id)
		self.cur.execute(stmt, args)
		self.con.commit()

	def add_test_user(
			self, user_id: int, name: str, university: str, gender: str, so: str,
			media_type: str, is_profile_complete: int
	) -> None:

		self.add_initial(user_id)
		self.add_name(user_id, name)
		self.add_university(user_id, university)
		self.add_gender(user_id, gender)
		self.add_so(user_id, so)
		self.add_media(user_id, media_type)

		if is_profile_complete:
			self.mark_profile_as_completed(user_id)

	def change_profile_step(self, user_id: int, profile_step: int) -> None:
		stmt = "UPDATE users SET profile_step = ? WHERE id = ?;"
		args = (profile_step, user_id)
		self.cur.execute(stmt, args)
		self.con.commit()

	def mark_profile_as_completed(self, user_id: int) -> None:
		stmt = "UPDATE users SET is_profile_complete = 1, profile_step = 10 WHERE id = ?;"
		args = (user_id,)
		self.cur.execute(stmt, args)
		self.con.commit()

	def get_user(self, user_id: int) -> dict or None:
		stmt = "SELECT * FROM users WHERE id = ?;"
		args = (user_id,)
		self.cur.execute(stmt, args)
		try:
			return dict(zip(user_attr, self.cur.fetchone()))
		except TypeError:
			return None

	def clear_tables(self) -> None:
		stmt = """
		DELETE FROM users;
		DELETE FROM matches;
		DELETE FROM pending_matches;"""
		self.cur.executescript(stmt)
		self.con.commit()

	def all_user_ids(self) -> list:
		stmt = "SELECT id FROM users"
		args = ()
		self.cur.execute(stmt, args)
		return self.cur.fetchmany()

	# pending matches functions
	def add_pending_match(self, user1: int, user2: int) -> None:
		stmt = f"""
		INSERT INTO pending_matches VALUES(?, ?, ?)"""
		args = (
			user1,
			user2,
			datetime_now()
		)
		print(stmt, args)
		self.cur.execute(stmt, args)
		self.con.commit()

	def get_pending_match(self, user_id: int) -> Any:
		stmt = "SELECT user2 FROM pending_matches WHERE user1 = ?"
		args = (
			user_id,
		)
		self.cur.execute(stmt, args)
		try:
			return self.cur.fetchone()[0]
		except TypeError:
			return None

	def delete_pending_match(self, user_id: int) -> None:
		stmt = "DELETE FROM pending_matches WHERE user1 = ?;"
		args = (
			user_id,
		)
		self.cur.execute(stmt, args)
		self.con.commit()

	# matches functions
	def add_match(self, user_id_1: int, user_id_2: int, action: int) -> None:
		stmt = "INSERT INTO matches VALUES (?, ?, ?, ?);"
		args = (
			user_id_1,
			user_id_2,
			action,
			datetime.now().strftime(date_time_format)
		)
		self.cur.execute(stmt, args)
		self.con.commit()

	def check_perfect_match(self, user_id_1: int, user_id_2: int) -> bool:
		stmt = "SELECT EXISTS(SELECT 1 FROM matches WHERE user1 = ? and user2 = ? and liked = 1)"
		args = (user_id_1, user_id_2)
		self.cur.execute(stmt, args)
		return self.cur.fetchone() == (1,)

	# find match for the user based on their gender and sexual orientation
	# genders are 'm' (male), 'f' (female)
	# sexual orientations (so) are 'homosexual' (o), 'heterosexual' (e), 'bisexual' (b)
	def get_next_swipe(self, user_id: int, gender: str, so: str) -> Any:
		if gender == 'm':
			g = 'm', 'f'
		elif gender == 'f':
			g = 'f', 'm'
		else:
			return None

		if so == 'o':
			gso = '{0}o|{0}b|{1}b'
		elif so == 'e':
			gso = '{1}e|{1}b'
		elif so == 'b':
			gso = '{0}o|{1}e|{0}b|{1}b'
		else:
			return None

		gso = gso.format(*g)

		gso = "(" + " OR ".join(f'(gender = "{pair[0]}" AND so = "{pair[1]}")' for pair in gso.split('|')) + ') AND '

		stmt = f"""
		SELECT id
		FROM users
		WHERE
			{gso}
			id NOT IN (
				SELECT user2
				FROM matches
				WHERE user1 = ?
			)
			AND id NOT IN (
				SELECT user1
				FROM matches
				WHERE user2 = ?
			)
			AND id != ? AND is_profile_complete = 1
			OR id IN (
				SELECT user1
				FROM matches
				WHERE user2 = ? AND liked = 1 AND user1 NOT IN (
					SELECT user2
					FROM matches
					WHERE user1 = ?
				)
			);"""

		print(stmt)

		args = (user_id,) * 5
		self.cur.execute(stmt, args)
		try:
			return self.cur.fetchone()[0]
		except TypeError:
			return None

	# complaints functions
	def add_complaint(self, user1: int, user2: int, complaint: int) -> None:
		stmt = "INSERT INTO complaints VALUES (?, ? ,?)"
		args = (
			user1,
			user2,
			complaint
		)
		self.cur.execute(stmt, args)
		self.con.commit()

	# errors functions
	def add_error(self, user_id: int, error_details: str) -> None:
		"""
		1. name error with '!'
		"""
		stmt = "INSERT INTO errors VALUES (?, ?, ?);"
		args = (
			user_id,
			error_details,
			datetime.now().strftime(date_time_format)
		)
		self.cur.execute(stmt, args)
		self.con.commit()

	def edit_user_attr(self, user_id: int, attr: str, v: str or int) -> None:
		stmt = f"UPDATE users SET {attr} = ? WHERE id = ?;"
		args = (v, user_id)
		self.cur.execute(stmt, args)
		self.con.commit()

	def delete_user(self, user_id):
		stmt = "DELETE FROM users WHERE id = ?;"
		args = (user_id,)
		self.cur.execute(stmt, args)
		self.con.commit()


pass
