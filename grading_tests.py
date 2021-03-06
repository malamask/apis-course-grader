import json

import requests

from db import Db
from logger import Logger
from result import Result
from settings import Settings

logger = Logger().logger
db = Db()


class GradingTests:

    def get_all_normal_count(self):
        results = []
        assignment = "Get request on /tweets"

        try:
            r = requests.get(Settings.ws_conn_string + '/tweets')

            if r.status_code == 200:
                results.append(Result(True, assignment, "Status code was 200"))
            else:
                results.append(Result(False, assignment, "Status code was not 200. Was " + str(r.status_code)))

            all_db_count = db.find_all().count()
            mapped_json_count = len(json.loads(r.content))
            if all_db_count == mapped_json_count:
                results.append(Result(True, assignment, "Our db count matched your returned count"))
            else:
                results.append(Result(False, assignment,
                                      "Our db count was: " + str(all_db_count)
                                      + ". Your service returned: " + str(mapped_json_count)))

            mapped_json = json.loads(r.content)
            results.append(Result(True, assignment, "All returned entities were tweets"))
            for single in mapped_json:
                if "id_str" not in single:
                    results.pop()
                    results.append(
                        Result(False, assignment, "Not all returned entities were tweets. Field id_str missing"))
                    break

        except requests.exceptions.RequestException as e:
            logger.warn(e)
            results.append(Result(False, assignment, str(e)))

        return results

    def get_all_greater_than(self):
        results = []
        assignment = 'Get request on /tweets using get parameter "morethan"'
        more_than = 3
        try:
            # normal request
            r = requests.get(Settings.ws_conn_string + '/tweets', params={'morethan': more_than})
            if r.status_code == 200:
                results.append(Result(True, assignment, "Status code was 200"))
            else:
                results.append(Result(False, assignment, "Status code was not 200. Was " + str(r.status_code)))

            # an to more_than einai string
            r = requests.get(Settings.ws_conn_string + '/tweets', params={'morethan': 'haltandcatchfire'})
            if r.status_code == 400:
                results.append(Result(True, assignment + ' str value', "Status code was " + str(r.status_code)))
            else:
                results.append(
                    Result(False, assignment + ' str value',
                           "Status code was " + str(r.status_code) + ". Should have been 400."))

            # an ta epistrefomena einai size > more_than
            r = requests.get(Settings.ws_conn_string + '/tweets', params={'morethan': more_than})
            mapped_json = json.loads(r.content)
            results.append(
                Result(True, assignment + ' hashtag count', 'All records had more hashtags than the minimum requested'))
            for m in mapped_json:
                if len(m['entities']['hashtags']) <= more_than:
                    results.pop()
                    results.append(
                        Result(False, assignment + ' hashtag count',
                               'Not all records had more hashtags than the minimum requested'))

            # an ta > more_than apo th diki mas db einai = me ta epistrefomena > more_than
            r = requests.get(Settings.ws_conn_string + '/tweets', params={'morethan': more_than})
            mapped_json = json.loads(r.content)
            more_than_count = db.find_with_hashtags_more_than(more_than).count()
            if len(mapped_json) == more_than_count:
                results.append(
                    Result(True, assignment + ' hashtag count db',
                           'Your service retured the correct amount of tweets'))
            else:
                results.append(
                    Result(False, assignment + ' hashtag count db',
                           'Your service did not return the correct amount of tweets.' +
                           ' Correct: ' + str(more_than_count) + ", Yours: " + str(len(mapped_json))))

        except requests.exceptions.RequestException as e:
            logger.warn(e)
            results.append(Result(False, assignment, str(e)))

        return results

    def get_all_with_hashtag(self):
        results = []
        hashtag = 'plastic'
        assignment = 'Get request on /tweets/hashtag/{tag} using tag "' + hashtag + '"'

        try:
            r = requests.get(Settings.ws_conn_string + '/tweets/hashtag/' + hashtag)

            if r.status_code == 200:
                results.append(Result(True, assignment, "Status code was 200"))
            else:
                results.append(Result(False, assignment, "Status code was not 200. Was " + str(r.status_code)))

            # ta returned na contain to hashtag oposdipote
            r = requests.get(Settings.ws_conn_string + '/tweets/hashtag/' + hashtag)
            mapped_json = json.loads(r.content)
            results.append(Result(True, assignment + ' all contain', 'All returned tweets contained the requested tag'))
            for m in mapped_json:
                tags = m['entities']['hashtags']
                failed = True
                for t in tags:
                    if t['text'] == hashtag:
                        failed = False
                if failed:
                    results.pop()
                    results.append(Result(True, assignment + ' all contain',
                                          'Not all returned tweets contained the requested tag'))
                    break

            # to count tis db na einai idio me to returned count
            r = requests.get(Settings.ws_conn_string + '/tweets/hashtag/' + hashtag)
            mapped_json_count = len(json.loads(r.content))
            db_count = db.find_with_hashtags(hashtag).count()
            if mapped_json_count == db_count:
                results.append(Result(True, assignment + ' hashtag count db',
                                      'Your service retured the correct amount of tweets'))
            else:
                results.append(
                    Result(False, assignment + ' hashtag count db',
                           'Your service did not return the correct amount of tweets.' +
                           ' Correct: ' + str(db_count) + ", Yours: " + str(len(mapped_json))))

        except requests.exceptions.RequestException as e:
            logger.warn(e)
            results.append(Result(False, assignment, str(e)))

        return results

    def delete_all_with_hashtag(self):
        results = []
        hashtag = 'deniparxei'
        assignment = 'Delete request on /tweets/hashtag/{tag} using tag "' + hashtag + '"'

        try:
            # req me troll hashtag. must return 0
            init_db_count = db.find_with_hashtags(hashtag).count()
            r = requests.delete(Settings.ws_conn_string + '/tweets/hashtag/' + hashtag)

            if r.status_code == 200:
                results.append(Result(True, assignment, "Status code was 200"))
            else:
                results.append(Result(False, assignment, "Status code was not 200. Was " + str(r.status_code)))

            after_db_count = db.find_with_hashtags(hashtag).count()

            if init_db_count == after_db_count:
                results.append(Result(True, assignment + ' count db',
                                      'Your service correctly did not delete any records'))
            else:
                results.append(Result(False, assignment + ' count db',
                                      'Your service mistakenly deleted some records'))

            # delete me kalo tag
            hashtag = 'earth'
            init_db_count = db.find_with_hashtags(hashtag).count()

            r = requests.delete(Settings.ws_conn_string + '/tweets/hashtag/' + hashtag)
            removed_count = r.json()['removedCount']
            after_db_count = db.find_with_hashtags(hashtag).count()
            if init_db_count - removed_count == after_db_count:
                results.append(Result(True, assignment + ' count db',
                                      'Your service correctly deleted ' + str(removed_count) + ' records'))
            else:
                results.append(Result(False, assignment + ' count db',
                                      'Your service reported '
                                      + str(removed_count) + ' deletions but actual was: '
                                      + str(int(init_db_count - after_db_count))))

        except requests.exceptions.RequestException as e:
            logger.warn(e)
            results.append(Result(False, assignment, str(e)))

        return results

    def simple_post(self):
        results = []
        assignment = 'Process a simple POST request'

        in_params = {'user': 'alex', 'message': 'o hai', 'age': '26'}
        try:
            r = requests.post(Settings.ws_conn_string + '/post', json=in_params)
            if r.status_code == 201:
                results.append(Result(True, assignment, "Status code was 201"))
            else:
                results.append(Result(False, assignment, "Status code was not 201. Was " + str(r.status_code)))

            # returned dict is same as input dict
            if len(r.json()) == 3 and 'user' in r.json() and 'message' in r.json() and 'age' in r.json():
                if r.json()['user'] == in_params['user'] and r.json()['user'] == in_params['user'] \
                        and r.json()['user'] == in_params['user']:
                    results.append(Result(True, assignment + ' dict check', "Response json was correct"))
                else:
                    results.append(
                        Result(False, assignment + ' dict check', "Response json was incorrect. Actual: " + r.json()))
            else:
                results.append(
                    Result(False, assignment + ' dict check', "Response json was incorrect. Actual: " + r.json()))

            # missing input values
            bad_in_params = {'asdf': 'alex', 'message': 'o hai', 'age': '26'}
            r = requests.post(Settings.ws_conn_string + '/post', json=bad_in_params)
            if r.status_code == 400:
                results.append(Result(True, assignment + ' bad input', "Status code was 400"))
            else:
                results.append(
                    Result(False, assignment + ' bad input', "Status code was not 400. Was " + str(r.status_code)))

        except requests.exceptions.RequestException as e:
            logger.warn(e)
            results.append(Result(False, assignment, str(e)))

        return results

    def get_full_tweet_text(self, tweet_map):
        text = ""
        if "extended_tweet" in tweet_map:
            text = tweet_map['extended_tweet']['full_text']
        else:
            text = tweet_map['text']

        return text
