import logging

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import ParseMode
from scraper import WikiRecommender
from custompersistence import CustomPersistence
from job import JobMetadata

# Enable logging
logging.basicConfig(format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level = logging.INFO)
logger = logging.getLogger(__name__)

def start(update, context):
    chat_id = update.message.chat_id
    update.message.reply_text('Hi! Send topics here to follow and get updated with\
 related Wikipedia articles.\n\n/set <number> hours/minutes to set the update interval.\
 Default is 24 hours.\n\n\
Report bugs and make feature requests at https://github.com/LakshyAAAgrawal/philomathbot')
    if 'job' in context.chat_data:
        old_jobs = context.job_queue.get_jobs_by_name(context.chat_data['job'].name)
        for old_job in old_jobs:
            old_job.schedule_removal()
    if 'recommender' in context.chat_data:
        recommender = context.chat_data["recommender"]
    else:
        recommender = WikiRecommender()
    new_context = {
        'recommender' : recommender,
        'chat_id' : chat_id
    }
    new_job = context.job_queue.run_repeating(
        send_link,
        86400,
        context = new_context,
        name = str(chat_id)
    )
    context.chat_data['job'] = JobMetadata(new_job.interval, new_job.name, new_context)
    context.chat_data['recommender'] = recommender

def stop(update, context):
    if 'job' in context.chat_data:
        old_jobs = context.job_queue.get_jobs_by_name(context.chat_data['job'].name)
        for old_job in old_jobs:
            old_job.schedule_removal()
    update.message.reply_text("You can start Receiving updates by sending /start")

def send_link(context):
    job = context.job
    recommender = job.context['recommender']
    chat_id = job.context['chat_id']
    title, summary, link = recommender.get_content()
    text = "*{}*\n{}\n[Full Article Here]({})".format(title, summary, link)
    context.bot.send_message(chat_id, text = text, parse_mode = ParseMode.MARKDOWN)

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
            old_jobs = context.job_queue.get_jobs_by_name(context.chat_data['job'].name)
            for old_job in old_jobs:
                old_job.schedule_removal()
        new_context = {
            'recommender' : recommender,
            'chat_id' : chat_id
        }
        new_job = context.job_queue.run_repeating(
            send_link,
            due,
            context = new_context,
            name = str(chat_id)
        )
        context.chat_data['job'] = JobMetadata(new_job.interval, new_job.name, new_context)
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

    pp = CustomPersistence(filename = config['DATA_STORAGE_FILENAME'])
    updater = Updater(config['API_TOKEN'], use_context=True, persistence = pp)
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
    for job_name in pp.get_custom_data()['job_queue']:
        job = pp.get_custom_data()['job_queue'][job_name]
        dp.job_queue.run_repeating(
            send_link,
            job.interval,
            context = job.context,
            name = job.name
        )
    # log all errors
    # dp.add_error_handler(error)
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
