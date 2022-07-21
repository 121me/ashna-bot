import string
from datetime import datetime
from functools import wraps

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import Updater, CommandHandler, MessageHandler, ConversationHandler, Filters, CallbackContext, \
	CallbackQueryHandler
from telegram.parsemode import ParseMode

import os
import re

from domains import domains

import random

from email_protocol import send_email
from ashna_secrets import API_KEY, VERIFY_PASS, LIST_OF_ADMINS

from translations import translate, detranslate

from names import check_name

from telegram import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from users import UsersDB
from pathlib import Path

# formats
date_time_format = "%Y.%m.%d.%H.%M.%S"

# databases
users_db = UsersDB()

# paths
media_path = f"{str(Path(__file__).parent.parent.absolute())}/profile-medias"

# lists
genders = 'male', 'female'
sos = 'homosexual', 'heterosexual', 'bisexual'
verify_methods = 'student_card', 'university_email_address'
steps = 'lang', 'name', 'age', 'gender', 'bio', 'last_saved_media_name',
steps_zip = list(enumerate(steps, start=0))

# dicts
rps_emojis = {
	'r': '🗿',
	'p': '📜',
	's': '✂️'
}

rps_cond = {
	'r': {
		'r': 0,
		'p': -1,
		's': 1
	},
	'p': {
		'r': 1,
		'p': 0,
		's': -1
	},
	's': {
		'r': -1,
		'p': 1,
		's': 0
	}
}

flag_and_language = {
	"🇹🇷": "tr",
	"🇬🇧": "en"
}

edit_options = {
	"gender": 1,
	"bio": 2,
	"so": 3,
	"language": 4,
	"media": 5
}

# keyboards
decision_keyboard = [
	[
		KeyboardButton("❤️"),
		KeyboardButton("👎"),
		# KeyboardButton("⛔"), TODO ADD LATER
		KeyboardButton("🚪")
	]
]

ok_nah_keyboard = [
	[
		KeyboardButton("OK 👍"),
		KeyboardButton("NAH 👎")
	]
]

language_keyboard = [
	[
		KeyboardButton("🇹🇷"),
		KeyboardButton("🇬🇧")
	]
]

rps_keyboard = [
	[
		InlineKeyboardButton(text='🗿', callback_data='r'),
		InlineKeyboardButton(text='📜', callback_data='p'),
		InlineKeyboardButton(text='✂️', callback_data='s')
	]
]


# generic keyboards
def big_keyboard_maker(kb: list) -> list:
	for b in kb:  # TODO REMEMBER, list[list[KeyboardButton]]
		pass
	return []


def edit_menu_keyboard(lan: str) -> list:
	vs = list(edit_options.keys())
	return [[KeyboardButton(translate(v, lan)) for v in vs[:2]],
			[KeyboardButton(translate(vs[2], lan))],
			[KeyboardButton(translate(v, lan)) for v in vs[3:]]]


def gender_keyboard(lan: str) -> list:
	return [[KeyboardButton(translate(g, lan)) for g in genders]]


def so_keyboard(lan: str) -> list:
	return [[KeyboardButton(translate(so_, lan)) for so_ in sos]]


def skip_keyboard(lan: str) -> list:
	return [[KeyboardButton(translate('skip', lan))]]


def verify_method_keyboard(lan: str) -> list:
	return [[KeyboardButton(translate(vm, lan)) for vm in verify_methods]]


def change_verify_method_keyboard(lan: str) -> list:
	return [[KeyboardButton(translate('change_vm', lan))]]


# markups
decision_reply_markup = ReplyKeyboardMarkup(
	decision_keyboard,
	one_time_keyboard=True,
	resize_keyboard=True
)

ok_nah_reply_markup = ReplyKeyboardMarkup(
	ok_nah_keyboard,
	one_time_keyboard=True,
	resize_keyboard=True
)

language_reply_markup = ReplyKeyboardMarkup(
	language_keyboard,
	one_time_keyboard=True,
	resize_keyboard=True
)


def edit_reply_markup(lan: str, choice: int):
	if choice == 1:
		return gender_reply_markup(lan)
	elif choice == 2:
		return skip_reply_markup(lan)
	elif choice == 3:
		return so_reply_markup(lan)
	elif choice == 4:
		return language_reply_markup
	return None


def edit_menu_reply_markup(lan: str):
	return ReplyKeyboardMarkup(
		edit_menu_keyboard(lan),
		one_time_keyboard=True,
		resize_keyboard=True)


def gender_reply_markup(lan: str):
	return ReplyKeyboardMarkup(
		gender_keyboard(lan),
		one_time_keyboard=True,
		resize_keyboard=True)


def so_reply_markup(lan: str):
	return ReplyKeyboardMarkup(
		so_keyboard(lan),
		one_time_keyboard=True,
		resize_keyboard=True)


def skip_reply_markup(lan: str):
	return ReplyKeyboardMarkup(
		skip_keyboard(lan),
		one_time_keyboard=True,
		resize_keyboard=True)


def verify_method_reply_markup(lan: str):
	return ReplyKeyboardMarkup(
		verify_method_keyboard(lan),
		one_time_keyboard=True,
		resize_keyboard=True)


def change_verify_method_reply_markup(lan: str):
	return ReplyKeyboardMarkup(
		change_verify_method_keyboard(lan),
		one_time_keyboard=True,
		resize_keyboard=True)


rps_inline_markup = InlineKeyboardMarkup(
	rps_keyboard
)

# states
(CHOOSING_LANG,
 TYPING_NAME,
 TYPING_AGE,
 CHOOSING_GENDER,
 TYPING_BIO,
 SENDING_MEDIA,
 CHOOSING_VERIFY_METHOD,
 SENDING_STUDENT_CARD,
 TYPING_EMAIL_ADDRESS,
 TYPING_VERIFY_CODE,
 IDLING) = range(11)

WAITING, TIMEOUT, DONE = range(-3, 0)

(CHOOSING_EDIT,
 EDITING_GENDER,
 EDITING_BIO,
 EDITING_SO,
 EDITING_LANGUAGE,
 EDITING_MEDIA) = range(6)

SWIPING, COMPLAINING = range(2)

DECISION, = range(1)

"""
profile_steps = {
	0: "language",
	1: "name",
	2: "age",
	3: "gender",
	4: "bio",
	5: "media",
	6: "verification method",
	7: "student card",
	8: "email address",
	9: "special code",
	10: "complete"
}
"""


def restricted(func):
	@wraps(func)
	def wrapped(update, context, *args, **kwargs):
		user_id = update.effective_user.id
		print(user_id)
		if user_id not in LIST_OF_ADMINS:
			print("Unauthorized access denied for {}.".format(user_id))
			return
		return func(update, context, *args, **kwargs)

	return wrapped


def verified(func):
	@wraps(func)
	def wrapped(update, context, *args, **kwargs):
		user_id = update.effective_user.id
		if user_id not in LIST_OF_ADMINS:
			pass

	return wrapped


# create profile handler commands
def start(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	if user_dict:
		if user_dict["is_profile_complete"]:
			update.effective_message.reply_text(
				text=translate("welcome_again_1", user_dict["lang"]))
			profile(update, context)
			return cancel(update, context)  # LOOK THERE LATER
		else:
			update.effective_message.reply_text(
				text=translate("welcome_again_2", user_dict["lang"]))
			return find_missing_for_profile(update, context)
	else:
		users_db.add_initial(user_id)

		update.effective_message.reply_text(
			text="Dil, Language?",
			reply_markup=language_reply_markup)
		print('here')
		return CHOOSING_LANG


def find_missing_for_profile(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	is_profile_complete = False

	for v, k in list(steps_zip):
		print(v, k)
		if not user_dict[k]:
			users_db.change_profile_step(user_id, v)
			print(k, v)
			profile_step = v
			break
	else:
		if user_dict["profile_step"] in [6, 7, 8, 9]:
			users_db.change_profile_step(user_id, 6)
			profile_step = CHOOSING_VERIFY_METHOD
		elif user_dict["profile_step"] in [10]:
			users_db.change_profile_step(user_id, 10)
			profile_step = IDLING
			is_profile_complete = user_dict["is_profile_complete"]
		else:
			profile_step = 0
			print("hey")

	lan = user_dict["lang"] or "en"

	if profile_step == 0:
		update.effective_message.reply_text(
			text=translate("send_lang", lan),
			reply_markup=language_reply_markup)

	elif profile_step == 1:
		update.effective_message.reply_text(
			text=translate("send_name", lan))

	elif profile_step == 2:
		update.effective_message.reply_text(
			text=translate("send_age", lan))

	elif profile_step == 3:
		update.effective_message.reply_text(
			text=translate("send_gender", lan),
			reply_markup=gender_reply_markup(lan))

	elif profile_step == 4:
		update.effective_message.reply_text(
			text=translate("send_bio", lan),
			reply_markup=skip_reply_markup(lan))

	elif profile_step == 5:
		update.effective_message.reply_text(
			text=translate("send_media", lan))

	elif profile_step == 6:
		update.effective_message.reply_text(
			text=translate("send_verify_method", lan),
			reply_markup=verify_method_reply_markup(lan))

	elif profile_step == 10:
		if is_profile_complete:
			update.effective_message.reply_text(
				text=translate("profile_completed", lan))
			profile(update, context)
			update.effective_message.reply_text(
				text=translate("main_menu", lan))
		else:
			update.effective_message.reply_text(
				text=translate("checking_profile", lan),
				reply_markup=rps_inline_markup)

	else:
		update.effective_message.reply_text(
			text=translate("send_verify_method", lan),
			reply_markup=verify_method_reply_markup(lan))

	return profile_step


def unknown_for_profile(update: Update, context: CallbackContext) -> int:
	content = update.message.text or 'media'

	update.effective_message.reply_text(
		text=f"unknown_for_profile: {content}")

	return find_missing_for_profile(update, context)


def lang_choice(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = lang(update, context)

	if result == 1:
		update.effective_message.reply_text(
			text=f"Language set to {update.effective_message.text}")  # TODO
		update.effective_message.reply_text(
			text=translate("new_user", user_dict["lang"]))
		return find_missing_for_profile(update, context)

	elif result == 0:
		update.effective_message.reply_text(text=translate(
			"lang_warning", user_dict["lang"]))
		return CHOOSING_LANG
	return CHOOSING_LANG


def name_choice(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = name(update, context)

	if result == 1:
		return find_missing_for_profile(update, context)

	elif result == 0:
		update.effective_message.reply_text(
			text=translate("name_warning", user_dict["lang"]))
		update.effective_message.reply_text(text=translate(
			"send_name", user_dict["lang"]))
		return TYPING_NAME

	elif result == -1:
		update.effective_message.reply_text(
			text=translate("send_name_but", user_dict["lang"]))
		update.effective_message.reply_text(text=translate(
			"send_name", user_dict["lang"]))
		return TYPING_NAME


def age_choice(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = age(update, context)

	if result == 1:
		return find_missing_for_profile(update, context)

	elif result == 0:
		update.effective_message.reply_text(
			text=translate("age_warning", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_age", user_dict["lang"]))
		return TYPING_AGE

	elif result == -1:
		update.effective_message.reply_text(
			text=translate("send_age_but", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_age", user_dict["lang"]))
		return TYPING_AGE


def gender_choice(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = gender(update, context)

	if result == 1:
		return find_missing_for_profile(update, context)

	elif result == 0:
		update.effective_message.reply_text(
			text=translate("gender_warning", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_gender", user_dict["lang"]))
		return CHOOSING_GENDER


def bio_choice(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = bio(update, context)

	if result == 1:
		return find_missing_for_profile(update, context)

	elif result == 0:
		update.effective_message.reply_text(
			text=translate("bio_skipped", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_media", user_dict["lang"]))
		return SENDING_MEDIA

	elif result == -1:
		update.effective_message.reply_text(
			text=translate("bio_warning", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_bio", user_dict["lang"]))
		return TYPING_BIO


"""
def university_choice(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    result = university(update, context)

    if result == 1:
        update.effective_message.reply_text(
            text=translate("send_media", user_dict["lang"]))
        return CHOOSING_MEDIA

    elif result == 0:
        update.effective_message.reply_text(
            text=translate("uni_warning", user_dict["lang"]))
        update.effective_message.reply_text(
            text=translate("send_uni", user_dict["lang"]))
        return TYPING_UNIVERSITY

    elif result == -1:
        update.effective_message.reply_text(
            text=translate("send_uni_but", user_dict["lang"]))
        update.effective_message.reply_text(
            text=translate("send_uni", user_dict["lang"]))
        return TYPING_UNIVERSITY
"""


def media_choice(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = media(update, context)

	if result == 1:
		return find_missing_for_profile(update, context)

	elif result == 0:
		update.effective_message.reply_text(
			text=translate("media_size_warning", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_media", user_dict["lang"]))
		return SENDING_MEDIA

	elif result == -1:
		update.effective_message.reply_text(
			text=translate("media_warning", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_media", user_dict["lang"]))
		return SENDING_MEDIA


def verify_method_choice(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = verify_method(update, context)

	if result == SENDING_STUDENT_CARD:
		update.effective_message.reply_text(
			text=translate("send_student_card", user_dict["lang"]))
		return SENDING_STUDENT_CARD
	elif result == TYPING_EMAIL_ADDRESS:
		update.effective_message.reply_text(
			text=translate("send_email_address", user_dict["lang"]))
		return TYPING_EMAIL_ADDRESS
	else:
		update.effective_message.reply_text(
			text=translate("verify_method_warning", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_verify_method", user_dict["lang"]))
		return CHOOSING_VERIFY_METHOD


def student_card_choice(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = student_card(update, context)

	if result == 1:
		update.effective_message.reply_text(
			text=translate("checking_profile", user_dict["lang"]),
			reply_markup=rps_inline_markup)
		send_message_to_admins(update, context, f'IDLING: {user_id}')
		return IDLING
	else:
		update.effective_message.reply_text(
			text=translate("student_card_warning", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_student_card", user_dict["lang"]))
		return SENDING_STUDENT_CARD


def email_address_choice(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = email_address(update, context)

	if result == 1:
		update.effective_message.reply_text(
			text=translate("send_verification_code", user_dict["lang"]))
		# create a verification code with 6 integers
		# save the verification code in the database
		# send verification code to user's email address
		user_dict = users_db.get_user(user_id)
		verify_code_ = ''.join(random.choices(string.digits, k=6))
		users_db.add_verify_code(user_id, verify_code_)
		send_email(user_dict["email_address"], verify_code_)
		return TYPING_VERIFY_CODE

	elif result == 0:
		update.effective_message.reply_text(
			text=translate("university_not_in_list", user_dict["lang"]).format(", ".join(domains.keys())))
		update.effective_message.reply_text(
			text=translate("send_verification_code", user_dict["lang"]))
		# create a verification code with 6 integers
		# save the verification code in the database
		# send verification code to user's email address
		user_dict = users_db.get_user(user_id)
		verify_code_ = ''.join(random.choices(string.digits, k=6))
		users_db.add_verify_code(user_id, verify_code_)
		send_email(user_dict["email_address"], verify_code_)
		return TYPING_VERIFY_CODE

	elif result == -1:
		update.effective_message.reply_text(
			text=translate("email_address_warning", user_dict["lang"]).format(", ".join(domains.keys())))
		update.effective_message.reply_text(
			text=translate("send_email_address", user_dict["lang"]))
		return TYPING_EMAIL_ADDRESS


def verify_code_choice(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = verify_code(update, context)

	if result == 1:
		update.message.reply_text(
			text=translate("checking_profile", user_dict["lang"]),
			reply_markup=rps_inline_markup)
		send_message_to_admins(update, context, f'IDLING: {user_id}')
		return IDLING
	elif result == 0:
		update.effective_message.reply_text(
			text=translate("verify_code_warning", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_verification_code", user_dict["lang"]))
		return TYPING_VERIFY_CODE


def rps_game(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	user_input = update.callback_query.data
	bot_input = str(random.choice(list(rps_emojis.keys())))

	result = rps_cond[user_input][bot_input]

	if result == 1:
		text = translate("rps_user_win", user_dict["lang"])
	elif result == -1:
		text = translate("rps_bot_win", user_dict["lang"])
	elif result == 0:
		text = translate("rps_draw", user_dict["lang"])
	else:
		text = "game_error"

	update.callback_query.answer()
	update.callback_query.edit_message_text(
		text=text.format(rps_emojis[user_input], rps_emojis[bot_input]),
		reply_markup=None
	)
	context.dispatcher.bot.send_message(
		chat_id=user_id,
		text=translate("rps_again", user_dict["lang"]),
		reply_markup=rps_inline_markup
	)
	return IDLING


def edit_profile(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	if user_dict["is_profile_complete"]:
		update.effective_message.reply_text(
			text=translate("edit_menu", user_dict["lang"]),
			reply_markup=edit_menu_reply_markup(user_dict["lang"]))
		return CHOOSING_EDIT

	update.effective_message.reply_text(
		text=translate("no_profile_no_command", user_dict["lang"])
	)
	return DONE


def choose_edit(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	try:
		user_input = update.effective_message.text

		if (input_user_edit_choice := detranslate(user_input)) in edit_options.keys():
			print(input_user_edit_choice)
			choice_state = edit_options[input_user_edit_choice]
		else:
			raise ValueError

	except (ValueError, TypeError):
		update.effective_message.reply_text(
			text=translate("send_valid", user_dict["lang"]))
		return CHOOSING_EDIT

	update.effective_message.reply_text(
		text=translate("send_your_thing", user_dict["lang"]).format(user_input),
		reply_markup=edit_reply_markup(user_dict["lang"], choice_state))
	return choice_state


def gender_edit(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = gender(update, context)

	if result == 1:
		return cancel(update, context)

	elif result == 0:
		update.effective_message.reply_text(
			text=translate("gender_warning", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_gender_c", user_dict["lang"]))
		return EDITING_GENDER


def bio_edit(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = bio(update, context)

	if result == 1:
		profile(update, context)
		return cancel(update, context)

	elif result == 0:
		update.effective_message.reply_text(
			text=translate("bio_skipped", user_dict["lang"]))
		profile(update, context)
		return cancel(update, context)

	elif result == -1:
		update.effective_message.reply_text(
			text=translate("bio_warning", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_bio_c", user_dict["lang"]))
		return EDITING_BIO


def so_edit(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = so(update, context)

	if result == 1:
		return cancel(update, context)
	elif result == 0:
		update.effective_message.reply_text(
			text=translate("so_warning", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_so_c", user_dict["lang"]))
		return EDITING_SO


def language_edit(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = lang(update, context)

	if result == 1:
		return cancel(update, context)
	elif result == 0:
		update.effective_message.reply_text(text=translate(
			"lang_warning", user_dict["lang"]))
		update.effective_message.reply_text(text=translate(
			"send_lang_c", user_dict["lang"]))
		return EDITING_LANGUAGE


def media_edit(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	result = media(update, context)

	if result == 1:
		profile(update, context)
		return cancel(update, context)

	elif result == 0:
		update.effective_message.reply_text(
			text=translate("media_warning", user_dict["lang"]))
		update.effective_message.reply_text(
			text=translate("send_media_c", user_dict["lang"]))
		return EDITING_MEDIA


def lang(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	input_flag = update.effective_message.text

	try:
		input_lang = flag_and_language[input_flag]
	except KeyError:
		return 0

	users_db.set_lang(user_id, input_lang)
	return 1


def name(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id

	try:
		input_name = update.effective_message.text.strip().replace('İ', 'i').replace('I', 'ı').lower()
	except AttributeError:
		return -1

	# check if the first character of input_name is '!' and others are alpha characters
	if input_name[:-1].isalpha() and 2 <= len(input_name.strip('!')) <= 20:
		if check_name(input_name):
			users_db.add_name(user_id, input_name)
			return 1
		elif input_name[-1] == '!':
			users_db.add_name(user_id, input_name.strip('!'))
			users_db.add_error(user_id, "name_warning")
			return 1
		return 0
	return -1


def calculate_age(birthday_str: str) -> int:
	try:
		birthday_dt = datetime.strptime(birthday_str, '%d.%m.%Y')
	except (ValueError, TypeError):
		return -1
	today = datetime.now()
	return today.year - birthday_dt.year - ((today.month, today.day) < (birthday_dt.month, birthday_dt.day))


def age(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	input_birthday = update.effective_message.text

	# DD.MM.YYYY
	# calculate age from input_birthday
	# if user is born in the future, return -1
	# if user is older than 18 years and younger than 30 years, return 1
	# else return -1

	user_age = calculate_age(input_birthday)

	if 18 <= user_age <= 29:
		users_db.add_age(user_id, input_birthday)
		return 1

	return -1 if user_age == -1 else 0


def gender(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	input_gender = detranslate(update.effective_message.text)

	if input_gender in ['m', 'f']:
		users_db.add_gender(user_id, input_gender)
		return 1
	return 0


def bio(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	input_bio = update.effective_message.text

	if input_bio:
		if input_bio == 'skip':  # TODO ADD TO TRANSLATE-no
			users_db.add_bio(user_id, 'no_bio')
			return 0
		if len(input_bio) >= 100 or input_bio.count('\n') >= 3:
			return -1
		users_db.add_bio(user_id, input_bio)
		return 1
	return -1


def media(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id

	# TODO check media size and video length
	if update.effective_message.photo:
		media_type = 'jpg'
		input_media = update.effective_message.photo[-1]
	elif update.effective_message.video:
		media_type = 'mp4'
		input_media = update.effective_message.video
	else:
		media_type = ''
		input_media = None

	# always .jpg or .mp4

	if input_media:
		# download and save image
		try:
			os.mkdir(f"{media_path}/{user_id}")
		except FileExistsError:
			pass

		users_db.add_media(user_id, media_type)
		last_saved_media_name = users_db.get_user(
			user_id)["last_saved_media_name"]

		input_media.get_file().download(
			f"{media_path}/{user_id}/{last_saved_media_name}.{media_type}")
		return 1
	return -1


def verify_method(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	verify_method_input = detranslate(update.effective_message.text)

	if verify_method_input == 'email':
		users_db.change_profile_step(user_id, TYPING_EMAIL_ADDRESS)
		return TYPING_EMAIL_ADDRESS
	elif verify_method_input == 'card':
		users_db.change_profile_step(user_id, SENDING_STUDENT_CARD)
		return SENDING_STUDENT_CARD
	return 0


def student_card(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id

	if update.effective_message.photo:
		input_student_card = update.effective_message.photo[-1]
	else:
		input_student_card = None

	# always .jpg or .mp4

	if input_student_card:
		# download and save image
		try:
			os.mkdir(f"{media_path}/{user_id}")
		except FileExistsError:
			pass

		# TODO add to database, change the profile step

		input_student_card.get_file().download(
			f"{media_path}/{user_id}/sc.jpg")
		users_db.change_profile_step(user_id, IDLING)
		return 1
	return -1


def email_address(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	email_address_input = update.effective_message.text

	if re.search(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+', email_address_input)\
and not users_db.check_email_address(email_address_input):

		_, domain = email_address_input.split('@')
		if "edu.tr" not in domain:
			return -1
		try:
			users_db.add_university(user_id, domains[domain])
			users_db.add_email_address(user_id, email_address_input)
			users_db.change_profile_step(user_id, TYPING_VERIFY_CODE)
			return 1
		except KeyError:
			users_db.add_university(user_id, domain)
			users_db.add_email_address(user_id, email_address_input)
			users_db.change_profile_step(user_id, TYPING_VERIFY_CODE)
			return 0
	return -1


def verify_code(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	input_verify_code = update.effective_message.text

	if users_db.check_verify_code(user_id, input_verify_code) or input_verify_code == VERIFY_PASS:
		users_db.change_profile_step(user_id, IDLING)
		return 1
	return 0


def so(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	so_input = update.effective_message.text

	user_so = detranslate(so_input)

	if user_so in ['e', 'o', 'b']:
		users_db.add_so(user_id, user_so)
		return 1
	return 0


def delete_profile_decision(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	update.effective_message.reply_text(
		text=translate("r_u_sure_delete_profile", user_dict["lang"]),
		reply_markup=ok_nah_reply_markup,
	)

	return DECISION


def delete_profile(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	input_decision = update.effective_message.text

	if input_decision == "OK 👍":
		users_db.delete_user(user_id)
		update.effective_message.reply_text(
			text=translate("profile_deleted", user_dict["lang"])
		)
		return DONE

	update.effective_message.reply_text(
		text=translate("profile_delete_cancelled", user_dict["lang"])
	)
	return cancel(update, context)


def help_(update: Update, context: CallbackContext) -> None:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	update.effective_message.reply_text(
		text=translate("help_command", user_dict["lang"]))
	"""
	if not user_dict[-1]:
		user_lost(update, context)
	"""


def about(update: Update, context: CallbackContext) -> None:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	update.effective_message.reply_text(
		text=translate("about", user_dict["lang"]),
		parse_mode=ParseMode.HTML,
		disable_web_page_preview=True)
	"""
	if not user_dict[-1]:
		user_lost(update, context)
	"""


def set_lang(update: Update, context: CallbackContext) -> None:
	pass  # TODO


def cancel(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	update.effective_message.reply_text(
		text=translate("main_menu", user_dict["lang"]))
	return DONE


def unknown(update: Update, context: CallbackContext) -> None:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	update.effective_message.reply_text(
		text=translate("unknown", user_dict["lang"]))


def warning(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	if user_dict["is_profile_complete"]:
		update.effective_message.reply_text(
			text=translate("swipe_warning",
						   user_dict["lang"]),
			reply_markup=ok_nah_reply_markup)
		return SWIPING

	update.effective_message.reply_text(
		text=translate("no_profile_no_command",
					   user_dict["lang"])
	)
	return DONE


def swipe(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	text = update.effective_message.text

	if text not in ["🚪", "OK 👍", "NAH 👎", "❤️", "👎", "⛔"]:
		print(5)
		unknown(update, context)
		return cancel(update, context)

	if text in ["🚪", "NAH 👎"]:
		return cancel(update, context)

	user_id_1 = user_id = update.effective_user.id
	user_id_2 = users_db.get_pending_match(user_id)

	if user_id_2:
		if text == "❤️":
			print(1)
			users_db.add_match(user_id_1, user_id_2, 1)

			if users_db.check_perfect_match(user_id_2, user_id_1):
				# TODO send both users each others link
				users_db.delete_pending_match(user_id)
				user_name_2 = users_db.get_user(user_id_2)["name"]
				user_name = user_dict["name"]
				update.effective_message.reply_text(
					text=translate("match_notification", users_db.get_user(
						user_id)["lang"]).format(user_id_2, user_name_2),
					parse_mode=ParseMode.HTML,
					disable_web_page_preview=True)
				try:
					context.dispatcher.bot.send_message(
						chat_id=user_id_2,
						text=translate("match_notification", users_db.get_user(
							user_id)["lang"]).format(user_id, user_name),
						parse_mode=ParseMode.HTML,
						disable_web_page_preview=True)
				except BadRequest:
					pass
				update.effective_message.reply_text(
					text=translate(
						"continue_swipe", user_dict["lang"]),
					reply_markup=ok_nah_reply_markup
				)
				return SWIPING

			else:
				print(2)
				swipe_user_id = users_db.get_next_swipe(user_id, user_dict['gender'], user_dict['so'])
				if swipe_user_id:
					send_swipe_profile(update, swipe_user_id)
					users_db.add_pending_match(user_id, swipe_user_id)
					return SWIPING
				else:
					users_db.delete_pending_match(user_id)
					update.effective_message.reply_text(
						text=translate("no_user", user_dict["lang"]))
					return cancel(update, context)

		elif text == "👎":
			users_db.add_match(user_id_1, user_id_2, 0)
			users_db.add_match(user_id_2, user_id_1, 0)

			swipe_user_id = users_db.get_next_swipe(user_id, user_dict['gender'], user_dict['so'])
			if swipe_user_id:
				send_swipe_profile(update, swipe_user_id)
				users_db.add_pending_match(user_id, swipe_user_id)
				return SWIPING

		elif text == "OK 👍":
			send_swipe_profile(update, user_id_2)
			return SWIPING

		elif text == "⛔":
			update.effective_message.reply_text(
				text=translate("", user_dict["lang"]))
			return COMPLAINING
		print(3)
	else:
		if text == "OK 👍":
			swipe_user_id = users_db.get_next_swipe(user_id, user_dict['gender'], user_dict['so'])
			if swipe_user_id:
				send_swipe_profile(update, swipe_user_id)
				users_db.add_pending_match(user_id, swipe_user_id)
				return SWIPING
			else:
				update.effective_message.reply_text(
					text=translate("no_user", user_dict["lang"]))
				return cancel(update, context)
		else:
			return cancel(update, context)
	print(4)


def complain(update: Update, context: CallbackContext) -> int:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	text = update.effective_message.text
	user_id_2 = users_db.get_pending_match(user_id)

	if text == "🎭":
		users_db.add_complaint(user_id, user_id_2, 1)
	elif text == "💸":
		users_db.add_complaint(user_id, user_id_2, 2)
	elif text == "🔞":
		users_db.add_complaint(user_id, user_id_2, 3)
	else:  # 🔙
		return SWIPING

	users_db.delete_pending_match(user_id)
	users_db.add_match(user_id, user_id_2, 0)
	users_db.add_match(user_id_2, user_id, 0)
	update.effective_message.reply_text(
		text=translate("continue_swipe", user_dict["lang"]),
		reply_markup=ok_nah_reply_markup)
	return SWIPING


# app commands

def profile(update: Update, context: CallbackContext) -> None:
	user_id = update.effective_user.id
	user_dict = users_db.get_user(user_id)

	if not user_dict["is_profile_complete"]:
		update.effective_message.reply_text(
			text=translate("no_profile_no_command", user_dict["lang"]),
		)
		return DONE

	user_media_path = f"""{media_path}/{user_id}/{user_dict["last_saved_media_name"]}.{user_dict["media_type"]}"""

	with open(file=user_media_path, mode="rb") as file:
		media_bytes = file.read()

	user_name, user_university = user_dict["name"].title(), user_dict["university"].title()

	print("hey", user_university, "hey")

	print(user_dict["media_type"])

	if user_dict["media_type"] == 'jpg':
		update.effective_message.reply_photo(
			photo=media_bytes,
			caption=f"""{user_name}, {calculate_age(user_dict["age"])}, {user_university}\n{'😁💬:'}{user_dict["bio"]
			if not user_dict["bio"] == "no_bio" else translate("no_bio", user_dict["lang"])}""",
		)
	elif user_dict["media_type"] == 'mp4':
		update.effective_message.reply_video(
			video=media_bytes,
			caption=f"""{user_name}, {calculate_age(user_dict["age"])}, {user_university}\n{'😁💬: '}{user_dict["bio"]
			if not user_dict["bio"] == "no_bio" else translate("no_bio", user_dict["lang"])}""",
		)
	else:
		update.effective_message.reply_text(
			text="error_report_this_2_admin"
		)


def send_swipe_profile(update: Update, swipe_user_id: int) -> None:
	user_dict = users_db.get_user(swipe_user_id)

	user_media_path = f"""{media_path}/{swipe_user_id}/{user_dict["last_saved_media_name"]}.{user_dict["media_type"]}"""

	with open(file=user_media_path, mode="rb") as file:
		media_bytes = file.read()

	user_name, user_university = user_dict["name"].title(), user_dict["university"].title()

	print(user_dict["media_type"])

	if user_dict["media_type"] == 'jpg':
		update.effective_message.reply_photo(
			photo=media_bytes,
			caption=f"""{user_name}, {calculate_age(user_dict["age"])}, {user_university}\n:{'😁💬:'}{user_dict["bio"]}""",
			reply_markup=decision_reply_markup
		)
	elif user_dict["media_type"] == 'mp4':
		update.effective_message.reply_video(
			video=media_bytes,
			caption=f"""{user_name}, {calculate_age(user_dict["age"])}, {user_university}\n:{'😁💬:'}{user_dict["bio"]}""",
			reply_markup=decision_reply_markup
		)
	else:
		update.effective_message.reply_text(
			text="error_report_this_2_admin"
		)


def send_message_to_admins(update: Update, context: CallbackContext, text: str) -> None:
	for admin_id in LIST_OF_ADMINS:
		context.dispatcher.bot.send_message(
			chat_id=admin_id,
			text=text)


@restricted
def set_user_attrs(update: Update, context: CallbackContext) -> None:
	# Message format: user_id user_attribute_1 value_1 user_attribute_2 value_2 ... user_attribute_n value_n
	text = update.effective_message.text
	try:
		_, user_id, *args = text.split()
	except ValueError:
		update.effective_message.reply_text(
			text="Message format: user_id user_attribute_1 value_1 user_attribute_2 value_2 ... user_attribute_n value_n")
		return
	print(user_id, args)
	user_id = int(user_id)

	# convert attrs to dictionary
	attrs_values = dict(zip(args[::2], args[1::2]))
	print(attrs_values)

	# update user attrs
	for attr, value in attrs_values.items():
		users_db.edit_user_attr(user_id, attr, value)


@restricted
def verify_user(update: Update, context: CallbackContext) -> None:
	text = update.effective_message.text
	user_ids = [int(i) for i in text.split()[1:]]

	for user_id in user_ids:
		user_dict = users_db.get_user(user_id)

		if not user_dict:
			update.effective_message.reply_text(
				text=f"User {user_id} not found")
			continue

		lan = user_dict['lang']

		users_db.mark_profile_as_completed(user_id)

		context.dispatcher.bot.send_message(
			chat_id=user_id,
			text=translate('profile_completed', lan))
		profile(update, context)
		update.effective_message.reply_text(
			text=translate("main_menu", lan))

		update.effective_message.reply_text(text=f"{user_id} marked as completed")  # map to list?


@restricted
def send_message_all_users(update: Update, context: CallbackContext, text: str) -> None:
	user_ids = users_db.all_user_ids()
	for user_id in user_ids:
		context.dispatcher.bot.send_message(
			chat_id=user_id,
			text=text)


def main():
	updater = Updater(token=API_KEY)
	dispatcher = updater.dispatcher

	try:
		os.mkdir(f"{media_path}")
	except FileExistsError:
		pass

	# create handlers
	verify_user_handler = CommandHandler('verify_user', verify_user)
	set_user_attrs_handler = CommandHandler('set_user_attrs', set_user_attrs)
	send_message_all_users_handler = CommandHandler('send_message_all_users', send_message_all_users)
	start_handler = CommandHandler('start', start)
	help_handler = CommandHandler('help', help_)
	about_handler = CommandHandler('about', about)
	profile_handler = CommandHandler('profile', profile)
	edit_profile_handler = CommandHandler('edit', edit_profile)
	delete_profile_handler = CommandHandler('delete', delete_profile_decision)
	cancel_handler = CommandHandler('cancel', cancel)

	# swipe conv entry
	warning_handler = CommandHandler('swipe', warning)

	# unknown command
	unknown_handler = MessageHandler(Filters.all, unknown)

	# create profile handler
	create_profile_conv_handler = ConversationHandler(
		entry_points=[start_handler],
		states={
			CHOOSING_LANG: [
				MessageHandler(
					Filters.text & (~Filters.command), lang_choice
				)
			],
			TYPING_NAME: [
				MessageHandler(
					Filters.text & (~Filters.command), name_choice
				)
			],
			TYPING_AGE: [
				MessageHandler(
					Filters.text & (~Filters.command), age_choice
				)
			],
			CHOOSING_GENDER: [
				MessageHandler(
					Filters.text & (~Filters.command), gender_choice
				)
			],
			TYPING_BIO: [
				MessageHandler(
					Filters.text & (~Filters.command), bio_choice
				)
			],
			SENDING_MEDIA: [
				MessageHandler(
					Filters.photo | Filters.video | Filters.video_note & (~Filters.text & ~Filters.command),
					media_choice
				)
			],
			CHOOSING_VERIFY_METHOD: [
				MessageHandler(
					Filters.text & (
						~Filters.command), verify_method_choice
				)
			],
			SENDING_STUDENT_CARD: [
				MessageHandler(
					Filters.photo & (~Filters.text & ~Filters.command), student_card_choice
				)
			],
			TYPING_EMAIL_ADDRESS: [
				MessageHandler(
					Filters.text & (
						~Filters.command), email_address_choice
				)
			],
			TYPING_VERIFY_CODE: [
				MessageHandler(
					Filters.text & (
						~Filters.command), verify_code_choice
				)
			],
			IDLING: [
				CallbackQueryHandler(
					rps_game, pattern='^r$|^p$|^s$'
				),
				MessageHandler(
					Filters.text & (
						~Filters.command), unknown
				)
			],
		},
		fallbacks=[
			help_handler,
			about_handler,
			MessageHandler(Filters.all, unknown_for_profile),
		]
	)

	edit_profile_conv_handler = ConversationHandler(
		entry_points=[edit_profile_handler],
		states={
			CHOOSING_EDIT: [
				MessageHandler(
					Filters.text & (~Filters.command), choose_edit
				)
			],
			EDITING_GENDER: [
				MessageHandler(
					Filters.text & (~Filters.command), gender_edit
				)
			],
			EDITING_BIO: [
				MessageHandler(
					Filters.text & (~Filters.command), bio_edit
				)
			],
			EDITING_SO: [
				MessageHandler(
					Filters.text & (~Filters.command), so_edit
				)
			],
			EDITING_LANGUAGE: [
				MessageHandler(
					Filters.text & (~Filters.command), language_edit
				)
			],
			EDITING_MEDIA: [
				MessageHandler(
					Filters.photo | Filters.video | Filters.video_note | Filters.text & (
						~Filters.command), media_edit
				)
			]
		},
		fallbacks=[
			help_handler,
			about_handler,
			cancel_handler,
		]
	)

	swipe_conv_handler = ConversationHandler(
		entry_points=[warning_handler],
		states={
			SWIPING: [
				MessageHandler(
					Filters.text & (~Filters.command), swipe
				)
			],
			COMPLAINING: [
				MessageHandler(
					Filters.text & (~Filters.command), complain
				)
			]
		},
		fallbacks=[
			help_handler,
			about_handler,
			cancel_handler,
		]
	)

	delete_profile_conv_handler = ConversationHandler(
		entry_points=[delete_profile_handler],
		states={
			DECISION: [
				MessageHandler(
					Filters.text & (~Filters.command), delete_profile
				)
			]
		}, fallbacks=[
			help_handler,
			about_handler,
			cancel_handler,
		]
	)

	handlers = [
		verify_user_handler,
		set_user_attrs_handler,
		send_message_all_users_handler,
		swipe_conv_handler,
		edit_profile_conv_handler,
		profile_handler,
		delete_profile_conv_handler,
		create_profile_conv_handler,
		unknown_handler,
	]
	# we add all handlers here

	for handler in handlers:
		dispatcher.add_handler(handler)

	updater.start_polling()
	updater.idle()


if __name__ == '__main__':
	main()
