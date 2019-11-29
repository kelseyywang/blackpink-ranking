import argparse
import json

from urllib.parse import urlparse, urlencode, parse_qs
from urllib.request import urlopen

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


YT_COMMENT_URL = 'https://www.googleapis.com/youtube/v3/commentThreads'
VIDEO_URL = 'https://www.youtube.com/watch?v=2S24-y0Ij3Y'
SONG_NAME = 'kill_this_love'

class RankMembers:
    def __init__(self):
        self.jennie = 0
        self.jisoo = 0
        self.lisa = 0
        self.rose = 0
        self.last_published_at = 'none'

    def get_comments_info(self, yt_url):
        # Referencing https://github.com/srcecde/python-youtube-api
        def load_comments():
            comments_arr = []
            for item in mat['items']:
                comment = item['snippet']['topLevelComment']
                text = comment['snippet']['textDisplay']
                likes = comment['snippet']['likeCount']
                published_at = comment['snippet']['publishedAt']
                comments_arr.append((text, likes, published_at))
            return comments_arr

        def open_url(url, params):
            f = urlopen(url + '?' + urlencode(params))
            data = f.read()
            f.close()
            matches = data.decode('utf-8')
            return matches

        parser = argparse.ArgumentParser()
        parser.add_argument('--key', help='Required API key')
        args = parser.parse_args()
        if not args.key:
            exit('Please specify API key using the --key=parameter.')

        video_id = urlparse(str(yt_url))
        q = parse_qs(video_id.query)
        vid = q['v'][0]

        params = {
            'part': 'snippet,replies',
            'videoId': vid,
            'key': args.key
        }
        all_comments_info = []
        matches = open_url(YT_COMMENT_URL, params)
        mat = json.loads(matches)
        next_pg_token = mat.get('nextPageToken')
        this_pg_comments = load_comments()
        analyzer = SentimentIntensityAnalyzer()
        all_comments_info.extend(this_pg_comments)
        self.add_average_sentiment(analyzer, this_pg_comments)
        count = 1
        with open('{}.txt'.format(SONG_NAME), 'a+') as file:  # Use file to refer to the file object
            while next_pg_token:
                params.update({'pageToken': next_pg_token})
                matches = open_url(YT_COMMENT_URL, params)
                mat = json.loads(matches)
                next_pg_token = mat.get('nextPageToken')
                this_pg_comments = load_comments()
                all_comments_info.extend(this_pg_comments)
                self.add_average_sentiment(analyzer, this_pg_comments)
                if count % 10 == 0:
                    print('Completed Page: ' + str(count) + ' with last published at ' + self.last_published_at)
                    print('Scores - Jennie: {}, Jisoo: {}, Lisa: {}, Rose: {}'.format(self.jennie, self.jisoo, self.lisa, self.rose))
                    file.write('Completed Page: ' + str(count) + ' with last published at ' + self.last_published_at + '\n')
                    file.write('Scores - Jennie: {}, Jisoo: {}, Lisa: {}, Rose: {}\n'.format(self.jennie, self.jisoo, self.lisa, self.rose))
                count += 1
        score_string = 'Final Scores - Jennie: {}, Jisoo: {}, Lisa: {}, Rose: {}'.format(self.jennie, self.jisoo, self.lisa, self.rose)
        return score_string

    def add_average_sentiment(self, analyzer, page_comments_info):
        # Using VADER: https://github.com/cjhutto/vaderSentiment
        for ci in page_comments_info:
            text, likes, published_at = ci
            self.last_published_at = published_at
            text = text.lower()
            compound_score = analyzer.polarity_scores(text)['compound']
            # Comments' sentiment ave weighted by number of likes
            weighted_score = (1 + likes) * compound_score
            if (weighted_score > 100 or weighted_score < -100) \
                and ('jennie' in text or 'jisoo' in text or 'ji-soo' in text 
                or 'ji soo' in text or 'lisa' in text or 'rose' in text or 'rosé' in text):
                # Print exceptionally large score-contributing comments
                print('\n\n EXCEPTIONAL COMMENT: {} with score {} and weight {}\n\n'.format(text, compound_score, 1 + likes))
            if 'jennie' in text:
                self.jennie += weighted_score
            if 'jisoo' in text or 'ji-soo' in text or 'ji soo' in text:
                self.jisoo += weighted_score
            if 'lisa' in text:
                self.lisa += weighted_score
            if 'rose' in text or 'rosé' in text:
                self.rose += weighted_score


if __name__ == '__main__':
    r = RankMembers()
    final_score_string = r.get_comments_info(VIDEO_URL)
    print(final_score_string)
    with open('final_{}.txt'.format(SONG_NAME), 'a+') as file:
        file.write(final_score_string)
