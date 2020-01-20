import logging

from telegram.ext import Updater, CommandHandler, PicklePersistence, MessageHandler, Filters
from scraper import WikiRecommender

# Enable logging
logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level = logging.INFO)
logger = logging.getLogger(__name__)

def start(update, context):
    chat_id = update.message.chat_id
    update.message.reply_text('Hi! Send topic names here to follow and get updated with\
related articles.\n/set <number> hours/minutes to set the update interval.')
    if 'job' in context.chat_data:
        old_job = context.chat_data['job']
        old_job.schedule_removal()
    if 'recommender' in context.chat_data:
        recommender = context.chat_data["recommender"]
    else:
        recommender = WikiRecommender()
    new_job = context.job_queue.run_repeating(send_link,
                                              86400,
                                              context = {'recommender' : recommender,
                                                         'chat_id' : chat_id})
    context.chat_data['job'] = new_job
    context.chat_data['recommender'] = recommender

def stop(update, context):
    if 'job' in context.chat_data:
        old_job = context.chat_data['job']
        old_job.schedule_removal()
    update.message.reply_text("You can start Receiving updates by sending /start")

def send_link(context):
    job = context.job
    recommender = job.context['recommender']
    chat_id = job.context['chat_id']
    title, summary = recommender.get_content()
    context.bot.send_message(chat_id, text=summary)

def set_interval(update, context):
    chat_id = update.message.chat_id
    recommender = context.chat_data["recommender"]
    try:
        due = int(context.args[0])
        if context.args[1] == 'hour' or context.args[1] == 'hours':
            due = due * 3600
        elif context.args[1] == 'minute' or context.args[1] == 'minutes':
            due = due * 60
        else:
            pass
        if due < 0 or due > 604800:
            update.message.reply_text('Sorry that is not a permissible value')
            return

        # Add job to queue and stop current one if there is a timer already
        if 'job' in context.chat_data:
            old_job = context.chat_data['job']
            old_job.schedule_removal()
        new_job = context.job_queue.run_repeating(send_link,
                                                  due,
                                                  context = {'recommender' : recommender,
                                                             'chat_id' : chat_id})
        context.chat_data['job'] = new_job
        update.message.reply_text('Interval successfully updated!')
    except (IndexError, ValueError):
        update.message.reply_text('Usage: /set <value> <unit(hour/minute)>')

def follow_topic(update, context):
    num_links = context.chat_data['recommender'].follow_topic(update.message.text)
    if num_links == 0:
        update.message.reply_text("Topic not found!")
    else:
        update.message.reply_text("{} new topics added".format(num_links))

def main():
    import json
    with open('config.json') as fp:
        config = json.load(fp)

    #pp = PicklePersistence(filename = config['DATA_STORAGE_FILENAME'])
    updater = Updater(config['API_TOKEN'], use_context=True)
    dp = updater.dispatcher

    # Add Handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(CommandHandler("stop", stop))
    dp.add_handler(CommandHandler("set",
                                  set_interval,
                                  pass_args = True,
                                  pass_job_queue = True,
                                  pass_chat_data = True))
    dp.add_handler(MessageHandler(Filters.text, follow_topic))
    #dp.add_handler(CommandHandler("addlink", addlink))
    #dp.add_handler(CommandHandler("removelink", removelink))

    # log all errors
    # dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
