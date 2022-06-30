from app.domains import domains

translations = {
	"en": {"main_menu": "1. /swipe other users\n"
						"2. /edit your profile\n"
						"3. preview your /profile",

		   "edit_menu": "1. Name\n"
						"2. Age\n"
						"3. Gender\n"
						"4. Bio\n"
						"5. Media\n"
						"6. /cancel",

		   "name": "name",
		   "age": "age",
		   "gender": "gender",
		   "bio": "bio",
		   "media": "media",
		   "email_address": "email address",
		   "verf_code": "verification code",

		   "new_user": "You are a new user!!! Let's create your profile first, shall we?",
		   "welcome_again_1": "You are already a member, welcome again 🥰",
		   "welcome_again_2": "Welcome again 🥰! You used to hang here but you forgot to add a few things to your profile",
		   "no_profile_no_method": "You have not created a profile to use this method yet, so type /start",
		   "send_your_thing": "Please send your {} to your profile",

		   "checking_profile": "Let me check your profile! When it is finished, an alert will be sent. Until then, let's play Rock, Paper, Scissors! Make your choice",
		   "rps_user_win": "Your choice-> {} {} <- My choice\nResult: You won!!!",
		   "rps_bot_win": "Your choice-> {} {} <- My choice\nResult: I won!!!",
		   "rps_draw": "Your choice-> {} {} <- My choice\nResult: Draw!!!",

		   "rps_again": "Let's play again, make your choice",

		   "profile_completed": "Welcome to Ashna!!! Your profile is completed and looks like this:",

		   "send_lang": "Dil, Language?",
		   "send_name": "Please enter your name:",
		   "send_age": "Please enter your age:",
		   "send_gender": "Please choose your gender:",
		   "send_bio": "Please write your bio with a few of sentences or skip it",
		   "send_media": "Please send a photo (less than 8mb) or a video (less than 20mb and 10 secs)",
		   "send_email_address": "Please enter your university email address:",
		   "send_verf_code": "Please enter the verification code that is sent to your email address",

		   "send_name_c": "Please enter your name or /cancel :",
		   "send_age_c": "Please enter your age or /cancel :",
		   "send_gender_c": "Please choose your gender or /cancel :",
		   "send_bio_c": "Please write your bio with a few of sentences or skip or /cancel :",
		   "send_media_c": "Please send a photo (less than 8mb) or a video (less than 20mb and 10 secs) or /cancel :",

		   "name_warning": "Please check your name and write it again. Remember, your name must be a Turkish name contain only letters. Also, you can add '!' at the end of your name and send it if you think something is wrong",
		   "age_warning": "Your age must be between 18 and 29 inclusive. Otherwise, do not use this app!!!",
		   "gender_warning": "Your gender must be male or female",
		   "bio_warning": "You skipped to enter your bio. You can add that later",
		   "media_warning": "Please check your media and send it again. Remember, your media must be either photo or video",
		   "email_address_warning": "Please check your university email address and write it again. Remember, it is available for the students from the following universities: {}".format(
			   ", ".join(domains.values())),
		   "verf_code_warning": "It did not matched!!! Please check the verification code and write it again",

		   "send_name_but": "Please send me nothing but your name!!!",
		   "send_age_but": "Please send me nothing but your age!!!",
		   "send_bio_but": "Please send me nothing but your bio!!!",
		   "send_media_but": "Please send me nothing but a photo or a video!!!",

		   "send_valid": "Please send a valid option or /cancel :",
		   "unknown": "Hey hey hey, you just sent something that I don't even know what to do with that. Type /help for more help if you are lost",

		   "about": "    Ashna Bot\n"
					"  2021-..\n"
					"Melih Aksoy\n\n"
					"It is a self-made project to practise coding, look at what I have done)))\n\n"
					"email : 125melih125@gmail.com\n"
					"github : <a href='https://www.github.com/121me'>121me</a>\n"
					"insta : <a href='https://www.instagram.com/pardonmyturkish'>pardonmyturkish</a>\n"
					"vk : <a href='https://www.vk.com/pardonmyturkish'>pardonmyturkish</a>\n",

		   "swipe_warning": "Reminder!\nKeep it in mind that there might be people impersonating someone else!\nProtect your privacy and DO NOT share any important personal information!",

		   "match_noti": '''MATCH!!! Start talking with <a href="tg://user?id={}">{}</a> (you cannot talk with the sample users for test)''',

		   "continue_swipe": "Do you want to continue swiping?",
		   "no_user": "There is no user out there for matching yet, check later again",

		   "complain_menu": "🎭 Impersonating someone / fake\n💸 Asking for money\n🔞 Adult material in profile\n🔙 Go back"}
}

detranslations = {
	# en
	"male": "m",
	"female": "f",
	"student card": "card",
	"university email address": "email",
}


def detranslate(name: str) -> str:
	try:
		return detranslations[name]
	except KeyError:
		return name


def translate(name: str, lan: str) -> str:
	try:
		return translations[lan][name]
	except KeyError:
		return name


if __name__ == '__main__':
	print(detranslate("male"))
	print(translate('about', 'en'))
