from aiogram.types import ReplyKeyboardMarkup,KeyboardButton,InlineKeyboardMarkup,InlineKeyboardButton


btnProfile = KeyboardButton('СТАРТ')
profileKeyboard = ReplyKeyboardMarkup(resize_keyboard=True).add(btnProfile)






btnUrlChannel = InlineKeyboardButton(text="ПОДПИСАТЬСЯ", url="https://t.me/openaichn")
btnDoneSub = InlineKeyboardButton(text="ПОДПИСАЛСЯ", callback_data="subchanneldone")

checkSubMenu = InlineKeyboardMarkup(row_width=1)
checkSubMenu.insert(btnUrlChannel)
checkSubMenu.insert(btnDoneSub)



