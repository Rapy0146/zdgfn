from aiogram import Router, F, Bot
from aiogram.filters import ExceptionMessageFilter, CommandObject, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.handlers import ErrorHandler
from aiogram.types import Message, CallbackQuery

from app.user.user_keyboard import *
from data.database.db import *
from app.payment import *
import data.config as config

router = Router()


class UserState(StatesGroup):
    send_message = State()


@router.message(Command("start"))
async def cmd_start(message: Message, command: CommandObject, state: FSMContext):
    if not get_users_exist(message.from_user.id):
        add_user_to_db(message.from_user.id)
        config.logger.info(f"Новый пользователь: @{message.from_user.username} - {message.from_user.id}")
    if command.args:
        u_id = command.args
        if u_id == str(message.from_user.id):
            await message.answer("❌Вы не можете отправить сообщение самому себе")
        elif get_users_exist(u_id):
            await message.answer(f"""Ты открыл(а) ссылку на '{config.bot_name}'.

Этот бот позволяет отправить анонимное сообщение другому пользователю Telegram.

Чтобы отправить сообщение, просто введи текст, фото или голосовое сообщение и нажми кнопку "Отправить".

Получатель сообщения никогда не узнает, кто его отправил.""", reply_markup=main_cancel_keyboard())
            await state.set_state(UserState.send_message)
            await state.update_data(u_id=u_id)
        else:
            await message.answer(f"""Я - '{config.bot_name}', бот, который позволяет отправлять анонимные сообщения другим пользователям Telegram.

            Если ты хочешь сказать кому-то что-то важное, но не хочешь, чтобы он знал, кто это говорит, то Тайное послание - это то, что тебе нужно.""",
                                 reply_markup=main_keyboard())
    else:
        await message.answer(f"""Я - '{config.bot_name}', бот, который позволяет отправлять анонимные сообщения другим пользователям Telegram.
        
Если ты хочешь сказать кому-то что-то важное, но не хочешь, чтобы он знал, кто это говорит, то Тайное послание - это то, что тебе нужно.""",
                             reply_markup=main_keyboard())


@router.message(F.text == "❌Отмена")
async def cancel(message: Message, state: FSMContext):
    await message.answer("Вы были возвращены в главное меню", reply_markup=main_keyboard())
    await state.clear()


@router.callback_query(F.data.startswith("cancel"))
async def cancel(call: CallbackQuery, state: FSMContext):
    try:
        await call.message.delete()
    except:
        pass
    await state.clear()


@router.message(F.text == "💼Профиль")
async def profile(message: Message):
    user_info = get_user_info(message.from_user.id)
    if user_info[2] == 0:
        status = "не активна"
    else:
        status = "Активна до " + user_info[3]
    text = f"""💼Профиль
        
🗓Дата регистрации: <i>{user_info[1]}</i>
📩Получено сообщений: <i>{user_info[5]}</i>
    
🔮Статус подписки: <i>{status}</i>
🧿Количество доступных просмотров: <i>{user_info[4]}</i>
    
📎Ваша ссылка: <code>t.me/{config.bot_username}?start={message.from_user.id}</code>"""
    await message.answer(text, parse_mode="HTML", reply_markup=profile_keyboard())
    try:
        await message.delete()
    except:
        pass


@router.callback_query(F.data.startswith("back_profile"))
async def profile(call: CallbackQuery):
    user_info = get_user_info(call.from_user.id)
    if user_info[2] == 0:
        status = "не активна"
    else:
        status = "Активна до " + user_info[3]
    text = f"""💼Профиль

🗓Дата регистрации: <i>{user_info[1]}</i>
📩Получено сообщений: <i>{user_info[5]}</i>

🔮Статус подписки: <i>{status}</i>
🧿Количество доступных просмотров: <i>{user_info[4]}</i>

📎Ваша ссылка: <code>t.me/{config.bot_username}?start={call.from_user.id}</code>"""
    await call.message.edit_text(text, parse_mode="HTML", reply_markup=profile_keyboard())


@router.message(F.text == "❓О боте")
async def about(message: Message):
    await message.answer(f"""<b>О боте</b>
<b>Бот "{config.bot_name}"</b> - это простой и удобный способ отправлять анонимные сообщения другим людям. Чтобы отправить сообщение, вам необходимо перейти по специальной ссылке и ввести сообщение, после бот отправит его получателю, но имя отправителя не будет видно.

<i>Преимущества бота:</i>

  <b>Анонимность</b>: вы можете отправлять сообщения, не раскрывая своего имени.
  <b>Простота</b>: отправить сообщение можно всего в несколько шагов.
  <b>Безопасность</b>: сообщения хранятся на серверах бота и доступны только вам и получателю.

<i>Как использовать бота:</i>

1. <b>Откройте чат с ботом по специальной ссылке</b>.
3. Введите <b>сообщение</b>.
4. Нажмите кнопку <b>"Отправить"</b>.

<i>Подписка "Отправитель"</i>

Подписка "Отправитель" позволяет вам видеть имя отправителя сообщений, которые вы получаете. Стоимость подписки составляет:

  1 месяц - <i>{config.subs_prices[0]} рублей</i>
  3 месяца - <i>{config.subs_prices[1]} рублей</i>
  12 месяцев - <i>{config.subs_prices[2]} рублей</i>

Чтобы приобрести подписку, откройте меню бота и выберите пункт <b>"Подписка"</b>.

<i>Контакты</i>

Если у вас есть вопросы или пожелания, вы можете связаться с разработчиком бота по контакту {config.admin_username}.
""", parse_mode="HTML", reply_markup=cancel_keyboard())
    try:
        await message.delete()
    except:
        pass


@router.message(UserState.send_message, F.text)
async def send_text_message(message: Message, state: FSMContext, bot: Bot):
    text = message.text
    data = await state.get_data()
    u_id = data.get("u_id")
    try:
        await bot.send_message(u_id, "📩Новое сообщение:\n\n" + text,
                               reply_markup=guess_keyboard(message.from_user.username, message.from_user.first_name))
        add_count_mess(u_id)
        await message.answer("✅Сообщение отправлено!", reply_markup=main_keyboard())
        await state.clear()
    except Exception as e:
        await message.answer("❌Произошла ошибка, попробуйте позже", reply_markup=main_keyboard())
        await state.clear()
        config.logger.error(e)


@router.message(UserState.send_message, F.photo)
async def send_photo_message(message: Message, state: FSMContext, bot: Bot):
    photo = message.photo[-1].file_id
    if message.caption:
        text = "\n\n" + message.caption
    else:
        text = ""
    data = await state.get_data()
    u_id = data.get("u_id")
    try:
        await bot.send_photo(u_id, photo, caption="📩Новое сообщение" + text,
                             reply_markup=guess_keyboard(message.from_user.username, message.from_user.first_name))
        add_count_mess(u_id)
        await message.answer("✅Сообщение отправлено!", reply_markup=main_keyboard())
        await state.clear()
    except Exception as e:
        await message.answer("❌Произошла ошибка, попробуйте позже", reply_markup=main_keyboard())
        await state.clear()
        config.logger.error(e)


@router.message(UserState.send_message, F.voice)
async def send_voice_message(message: Message, state: FSMContext, bot: Bot):
    voice = message.voice.file_id
    data = await state.get_data()
    u_id = data.get("u_id")
    try:
        await bot.send_voice(u_id, voice, caption="📩Новое сообщение",
                             reply_markup=guess_keyboard(message.from_user.username, message.from_user.first_name))
        add_count_mess(u_id)
        await message.answer("✅Сообщение отправлено!", reply_markup=main_keyboard())
        await state.clear()
    except Exception as e:
        await message.answer("❌Произошла ошибка, попробуйте позже", reply_markup=main_keyboard())
        await state.clear()
        config.logger.error(e)


@router.message(UserState.send_message, F.document)
async def send_document_message(message: Message, state: FSMContext, bot: Bot):
    document = message.document.file_id
    if message.caption:
        text = "\n\n" + message.caption
    else:
        text = ""
    data = await state.get_data()
    u_id = data.get("u_id")
    try:
        await bot.send_document(u_id, document, caption="📩Новое сообщение" + text,
                                reply_markup=guess_keyboard(message.from_user.username, message.from_user.first_name))
        add_count_mess(u_id)
        await message.answer("✅Сообщение отправлено!", reply_markup=main_keyboard())
        await state.clear()
    except Exception as e:
        await message.answer("❌Произошла ошибка, попробуйте позже")
        await state.clear()
        config.logger.error(e)


@router.message(UserState.send_message, F.audio)
async def send_audio_message(message: Message, state: FSMContext, bot: Bot):
    audio = message.audio.file_id
    if message.caption:
        text = "\n\n" + message.caption
    else:
        text = ""
    data = await state.get_data()
    u_id = data.get("u_id")
    try:
        await bot.send_audio(u_id, audio, caption="📩Новое сообщение" + text,
                             reply_markup=guess_keyboard(message.from_user.username, message.from_user.first_name))
        add_count_mess(u_id)
        await message.answer("✅Сообщение отправлено!", reply_markup=main_keyboard())
        await state.clear()
    except Exception as e:
        await message.answer("❌Произошла ошибка, попробуйте позже", reply_markup=main_keyboard())
        await state.clear()
        config.logger.error(e)


@router.message(UserState.send_message, F.video)
async def send_video_message(message: Message, state: FSMContext, bot: Bot):
    video = message.video.file_id
    if message.caption:
        text = "\n\n" + message.caption
    else:
        text = ""
    data = await state.get_data()
    u_id = data.get("u_id")
    try:
        await bot.send_video(u_id, video, caption="📩Новое сообщение" + text,
                             reply_markup=guess_keyboard(message.from_user.username, message.from_user.first_name))
        add_count_mess(u_id)
        await message.answer("✅Сообщение отправлено!", reply_markup=main_keyboard())
        await state.clear()
    except Exception as e:
        await message.answer("❌Произошла ошибка, попробуйте позже", reply_markup=main_keyboard())
        await state.clear()
        config.logger.error(e)


@router.message(UserState.send_message, F.video_note)
async def send_video_note_message(message: Message, state: FSMContext, bot: Bot):
    video_note = message.video_note.file_id
    data = await state.get_data()
    u_id = data.get("u_id")
    try:
        await bot.send_message(u_id, "📩Новое сообщение:")
        await bot.send_video_note(u_id, video_note,
                                  reply_markup=guess_keyboard(message.from_user.username, message.from_user.first_name))
        add_count_mess(u_id)
        await message.answer("✅Сообщение отправлено!", reply_markup=main_keyboard())
        await state.clear()
    except Exception as e:
        await message.answer("❌Произошла ошибка, попробуйте позже", reply_markup=main_keyboard())
        await state.clear()
        config.logger.error(e)


@router.message(UserState.send_message, F.animation)
async def send_animation_message(message: Message, state: FSMContext, bot: Bot):
    animation = message.animation.file_id
    if message.caption:
        text = "\n\n" + message.caption
    else:
        text = ""
    data = await state.get_data()
    u_id = data.get("u_id")
    try:
        await bot.send_animation(u_id, animation, caption="📩Новое сообщение" + text,
                                 reply_markup=guess_keyboard(message.from_user.username, message.from_user.first_name))
        add_count_mess(u_id)
        await message.answer("✅Сообщение отправлено!", reply_markup=main_keyboard())
        await state.clear()
    except Exception as e:
        await message.answer("❌Произошла ошибка, попробуйте позже", reply_markup=main_keyboard())
        await state.clear()
        config.logger.error(e)


@router.message(UserState.send_message, F.sticker)
async def send_sticker_message(message: Message, state: FSMContext, bot: Bot):
    sticker = message.sticker.file_id
    data = await state.get_data()
    u_id = data.get("u_id")
    try:
        await bot.send_message(u_id, "📩Новое сообщение:")
        await bot.send_sticker(u_id, sticker,
                               reply_markup=guess_keyboard(message.from_user.username, message.from_user.first_name))
        add_count_mess(u_id)
        await message.answer("✅Сообщение отправлено!", reply_markup=main_keyboard())
        await state.clear()
    except Exception as e:
        await message.answer("❌Произошла ошибка, попробуйте позже", reply_markup=main_keyboard())
        await state.clear()
        config.logger.error(e)


@router.callback_query(F.data.startswith("guess"))
async def guess(call: CallbackQuery, state: FSMContext):
    data = call.data.split(":")
    username = data[1]
    name = data[2]
    if check_subscription(call.from_user.id):
        await call.message.answer(f"🫣Отправитель: {name} -> @{username}")
    elif check_bought_views(call.from_user.id) != 0:
        await call.message.answer(
            f"У вас осталось {check_bought_views(call.from_user.id)} просмотров. Хотите просмотреть отправителя?",
            reply_markup=quest_keyboard())
        await state.update_data(username=username, name=name)
    else:
        await call.message.answer("❌ У вас закончились просмотры. Хотите купить еще?",
                                  reply_markup=ask_buy_views_keyboard())


@router.callback_query(F.data.startswith("subscription"))
async def subscription(call: CallbackQuery):
    await call.message.edit_text(f"""<b>Хочешь знать, кто тебе пишет в боте '{config.bot_name}'?</b>

<b>Приобрети подписку</b> и получай полную информацию о сообщениях, которые тебе приходят.

<b>Преимущества подписки:</b>

  <i>Безопасность:</i> ты будешь уверен, что получаешь сообщения от того человека, от которого ожидаешь.
  <i>Контроль:</i> ты можешь контролировать, от кого ты получаешь сообщения.
  <i>Интерес:</i> общение может стать более интригующим.

<b>Стоимость подписки:</b>

  1 месяц - <i>{config.subs_prices[0]} рублей</i>
  3 месяца - <i>{config.subs_prices[1]} рублей</i>
  12 месяцев - <i>{config.subs_prices[2]} рублей</i>

<b>Выберите срок подписки:</b>
""", parse_mode="HTML", reply_markup=subscription_keyboard())


@router.callback_query(F.data.startswith("buy_subscription"))
async def but_subscription(call: CallbackQuery, state: FSMContext):
    month = call.data.split(":")[1]
    text = call.data.split(":")[2]
    await state.update_data(month=month)
    price = get_subscription_price(month)
    p_id, link = create_payment()
    if check_subscription(call.from_user.id):
        await call.message.edit_text("❌У вас уже есть активная подписка", reply_markup=subscription_info_keyboard())
    else:
        await call.message.edit_text(f"""Вы выбрали подписку на {month} {text}.
        
<b>Стоимость подписки:</b> <i>{price} рублей</i>

Оплачивая подписку, вы принимаете Правила конфиденциальности, Условия подписки и Правила пользования программы.
Ознакомится с ними можно по ссылкам: https://telegra.ph/Politika-v-otnoshenii-obrabotki-personalnyh-dannyh-04-03-25

Что бы оплатить, перейдите по ссылке ниже, после оплаты нажмите <b>Проверить оплату</b>""", parse_mode="HTML",
                                     reply_markup=buy_subscription_keyboard(link, p_id))


@router.callback_query(F.data.startswith("check_subscription_pay"))
async def check_pay(call: CallbackQuery, state: FSMContext, bot: Bot):
    p_id = call.data.split(":")[1]
    if check_payment(p_id):
        data = await state.get_data()
        month = data.get("month")
        add_subscription(call.from_user.id, month)
        await call.message.edit_text("✅Оплата прошла успешно. Подписка активирована",
                                     reply_markup=subscription_info_keyboard())
    else:
        await call.answer("❌Оплата не найдена")


@router.callback_query(F.data.startswith("views"))
async def views(call: CallbackQuery):
    await call.message.edit_text(f"""<b>Купить просмотры</b>

Просмотр сообщения - это возможность узнать, кто отправил тебе сообщение, не приобретая подписку.

<b>Стоимость просмотра:</b> <i>{config.view_price} рублей</i>

<b>Выберите количество просмотров:</b>""", parse_mode="HTML", reply_markup=views_keyboard())


@router.callback_query(F.data.startswith("buy_views"))
async def buy_views(call: CallbackQuery, state: FSMContext):
    count = call.data.split(":")[1]
    await state.update_data(count=count)
    p_id, link = create_payment()
    await call.message.edit_text(f"""Вы выбрали <b>{count}</b> просмотров.

<b>Стоимость просмотров:</b> <i>{int(count) * config.view_price} рублей</i>

Оплачивая, вы принимаете Правила конфиденциальности, Условия подписки и Правила пользования программы.
Ознакомится с ними можно по ссылкам: https://telegra.ph/Politika-v-otnoshenii-obrabotki-personalnyh-dannyh-04-03-25

Что бы оплатить, перейдите по ссылке ниже, после оплаты нажмите <b>Проверить оплату</b>""", parse_mode="HTML",
                                     reply_markup=buy_views_keyboard(link, p_id))


@router.callback_query(F.data.startswith("check_views_pay"))
async def check_pay(call: CallbackQuery, state: FSMContext):
    p_id = call.data.split(":")[1]
    if check_payment(p_id):
        data = await state.get_data()
        count = data.get("count")
        add_views(call.from_user.id, count)
        await call.message.edit_text("✅Оплата прошла успешно. Просмотры зачислены",
                                     reply_markup=subscription_info_keyboard())
    else:
        await call.answer("❌Оплата не найдена")


@router.callback_query(F.data.startswith("quest"))
async def quest(call: CallbackQuery, state: FSMContext):
    answer = call.data.split(":")[1]
    if answer == "yes":
        if check_bought_views(call.from_user.id) > 0:
            data = await state.get_data()
            username = data.get("username")
            name = data.get("name")
            subtract_bought_views(call.from_user.id)
            try:
                await call.message.delete()
            except:
                pass
            await call.message.answer(f"🫣Отправитель: {name} -> @{username}")
    else:
        try:
            await call.message.delete()
        except:
            pass
         

# Ловим ошибки
@router.errors(ExceptionMessageFilter(
    "Telegram server says - Bad Request: message is not modified: specified new message content and reply markup are exactly the same as a current content and reply markup of the message")
)
class MyHandler(ErrorHandler):
    async def handle(self):
        pass


@router.error()
class MyHandler(ErrorHandler):
    async def handle(self):
        print(self.exception_name)
        print(self.exception_message[self.exception_message.find("exception="):])
        config.logger.error(self.exception_name + " | " + self.exception_message[self.exception_message.find("exception="):])



 
