import os
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, InlineQueryHandler
from googleapiclient.discovery import build
from google.cloud import dialogflow

# Telegram bot token
TELEGRAM_TOKEN = '6907328219:AAFVsJavqjXRoO-rDBfZv4Su9pyYUQYTWck'

# Google API credentials
GOOGLE_API_KEY = 'AIzaSyAUZjfyMKSQv5qJxttHRsSqW0VhBk8YxOk'
FACT_CHECK_API_VERSION = 'v1alpha1'
FACT_CHECK_API_SERVICE_NAME = 'factchecktools'

# Bard API config
BARD_PROJECT_ID = "facthunter-c676e"  # Replace with your project ID
BARD_SERVICE_ACCOUNT_KEY_FILE = 'C:\\Users\\ACER\\Desktop\\dailama'
# File to store user requests
LOG_FILE = 'user_requests.log'


def start(update: Update, context: CallbackContext) -> None:
    user_name = update.message.from_user.username
    update.message.reply_text(f'Welcome to FactHunter Bot, {user_name}! Text me a piece of news, and I will check if it is fake.\nFeel free to give feedback at WhatsApp on 8309173896.')


def check_fake_news(update: Update, context: CallbackContext) -> None:
    user_name = update.message.from_user.username
    user_message = update.message.text

    # Log the user's message with their name and response
    result = check_fact_check_explorer(user_message)
    log_user_message(user_name, user_message, result)

    feedback_message = "Feel free to give feedback at WhatsApp on 8309173896."
    response_message = f"\nResult: {result}\n\n{feedback_message}"
    update.message.reply_text(response_message)


def log_user_message(user_name: str, message: str, response: str) -> None:
    with open(LOG_FILE, 'a') as log_file:
        log_file.write(f"User: {user_name}\nMessage: {message}\nResponse: {response}\n\n")


def check_fact_check_explorer(claim: str) -> str:
    service = build(FACT_CHECK_API_SERVICE_NAME, FACT_CHECK_API_VERSION, developerKey=GOOGLE_API_KEY)

    try:
        request = service.claims().search(query=claim)
        response = request.execute()

        if 'claims' in response:
            claims = response['claims']
            if claims:
                claim_review = claims[0].get('claimReview', [])
                if claim_review:
                    result = claim_review[0].get('text', 'Result not available.')
                    publication_date = claim_review[0].get('publishDate', 'Date not available.')
                    url = claim_review[0].get('url', 'URL not available.')

                    response_message = f"\nClaim: {claim}\nURL: {url}"

                    return response_message

        bard_response = generate_bard_response(claim)
        return bard_response

    except Exception as e:
        print(f"An error occurred: {e}")
        return 'An error occurred while processing the request.'


def generate_bard_response(claim: str) -> str:
    session_client = dialogflow.SessionsClient.from_service_account_json(BARD_SERVICE_ACCOUNT_KEY_FILE)
    session_path = session_client.session_path(BARD_PROJECT_ID, "fact-hunter-session")
    query_text = dialogflow.QueryInput(text=claim)
    response = session_client.detect_intent(session_path, query_text)
    return response.query_result.fulfillment_text


def inline_query(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    if not query:
        return

    results = []
    response_message = check_fact_check_explorer(query)

    results.append(
        InlineQueryResultArticle(
            id=update.inline_query.id,
            title="Fact Check Result",
            input_message_content=InputTextMessageContent(response_message),
        )
    )

    update.inline_query.answer(results)


def main() -> None:
    updater = Updater(TELEGRAM_TOKEN)

    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, check_fake_news))
    dp.add_handler(InlineQueryHandler(inline_query))

    updater.start_polling()

    updater.idle()


if __name__ == '__main__':
    main()
