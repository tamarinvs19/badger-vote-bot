import datetime
import logging

from sqlalchemy.orm import Session
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, filters, PollAnswerHandler

from models import Suggestion, Base, Vote
from storage import Storage
import database

import config as cfg


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


Base.metadata.create_all(bind=database.engine)


button_help = KeyboardButton('/help')
button_list = KeyboardButton('/list')

greet_kb = ReplyKeyboardMarkup([[button_help, button_list]], True)


async def start_bot(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    await update.message.reply_text(
        f'Привет, {user.full_name}!',
        reply_markup=greet_kb
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_markdown(
        """
        Здесь можно предложить свой вариант музыки на подъем.
        
        *Команды*
            /help : Вывести это сообщение 
            /list : Посмотреть список предложений и проголосовать 
            /add `<название трека>` : Добавить свой вариант 
        
        *Особенности*
            За один день можно предложить только один трек.
            Голосовать можно сколько угодно раз, сохраняется только последний голос.
            Результаты скрыты, чтобы сохранялась интрига)
        """,
        reply_markup=greet_kb,
    )


async def show_suggestion_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all suggestions."""

    suggestions = list(Storage().suggestions.values())

    if len(suggestions) == 0:
        await update.message.reply_text(f"Предложений нет")
    elif len(suggestions) == 1:
        await update.message.reply_text(f"Сейчас только одно предложение: {suggestions[0].text}")
    else:
        today = datetime.datetime.today()
        tomorrow = today + datetime.timedelta(days=1)
        suggestion_texts, suggestion_ids = list(zip(*[
            (suggestion.text, suggestion.pk)
            for suggestion in suggestions
        ]))
        logger.debug(suggestion_texts)

        message = await context.bot.send_poll(
            update.effective_chat.id,
            "Список предложений:",
            suggestion_texts,
            False,
            allows_multiple_answers=False,
            close_date=tomorrow
        )
        payload = {
            message.poll.id: {
                "suggestion_ids": suggestion_ids,
                "message_id": message.message_id,
                "chat_id": update.effective_chat.id,
                "answers": 0,
            }
        }
        context.bot_data.update(payload)


async def add_suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add new suggestion."""

    suggestion_text = ' '.join(context.args)
    storage = Storage()
    if len(suggestion_text.strip()) == 0:
        await update.message.reply_text(
            "Слишком короткое название! Пример корректной команды: /add Имперский марш",
            reply_markup=greet_kb,
        )
    elif storage.can_user_add_suggestion_today(update.effective_user.id):
        storage.add_suggestion(
            Suggestion(
                text=suggestion_text,
                creator_id=update.effective_user.id,
                created_at=datetime.datetime.today(),
            )
        )
        await update.message.reply_text(
            "Добавил!",
            reply_markup=greet_kb,
        )
    else:
        await update.message.reply_text(
            "За день можно добавить свой вариант только один раз!",
            reply_markup=greet_kb,
        )


async def poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Poll answer handler"""

    answer = update.poll_answer
    answered_poll = context.bot_data[answer.poll_id]

    try:
        suggestion_ids = answered_poll["suggestion_ids"]
    except KeyError:
        return

    selected_options = answer.option_ids
    for option_id in selected_options:
        user_id = update.effective_user.id
        storage = Storage()
        session = storage.session
        if user_id in storage.votes:
            session.delete(storage.votes[user_id])
        session.add(
            Vote(user_id=update.effective_user.id, suggestion_id=suggestion_ids[option_id])
        )
        session.commit()

    await context.bot.send_message(
        chat_id=answered_poll['chat_id'],
        text="Голос принят!",
        reply_to_message_id=answered_poll['message_id'],
        reply_markup=greet_kb,
    )


async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show all results."""

    suggestions = Storage().get_results()
    if len(suggestions) == 0:
        await update.message.reply_text(
            "Нет ни одного предложения!",
        )
    else:
        await update.message.reply_text(
            "\n".join([
                f"{suggestion}: {count}"
                for suggestion, count in suggestions.items()
            ]),
        )


async def clear_votes(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete all votes."""

    most_common = Storage().clear()
    await update.message.reply_text(f"Самое популярное: {most_common}")


async def remove_suggestion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete suggestion."""

    suggestion_id = context.args[0]
    Storage().remove_suggetion(suggestion_id)
    await update.message.reply_text(f"Удалено: {suggestion_id}")


def main() -> None:
    """Start the bot."""

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(cfg.TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start_bot))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("list", show_suggestion_list))
    application.add_handler(CommandHandler("add", add_suggestion))
    application.add_handler(CommandHandler("results", show_results, filters.User(username="@vtamarin")))
    application.add_handler(CommandHandler("clear", clear_votes, filters.User(username="@vtamarin")))
    application.add_handler(CommandHandler("remove", remove_suggestion, filters.User(username="@vtamarin")))

    application.add_handler(PollAnswerHandler(poll_answer))

    application.run_webhook(
        listen="0.0.0.0",
        port=cfg.PORT,
        url_path=cfg.TOKEN,
        webhook_url=f'https://{cfg.APPNAME}.herokuapp.com/' + cfg.TOKEN,
    )


if __name__ == "__main__":
    main()
