import pytumblr
import markdownify
import time
import textwrap
import re
from secrets import CONSUMER_KEY, OAUTH_SECRET, SECRET_KEY, OAUTH_TOKEN, blog

client = pytumblr.TumblrRestClient(
    CONSUMER_KEY,
    SECRET_KEY,
    OAUTH_TOKEN,
    OAUTH_SECRET
)

author_regex = r"^\s*by ([A-Z][a-z]+ [A-Z][a-z]+)\s+"

def process_post(post, post_num):
    poem_text = post['body']

    # strip extranous formatting and text, convert to markdown
    poem_text = poem_text.replace("<blockquote>", "")
    poem_text = poem_text.replace("<\blockquote>", "")

    poem_text_md = markdownify.markdownify(poem_text)
    poem_lines = poem_text_md.split("\n")

    if ("media.tumblr.com" in poem_text):
        alert_for_manual_check(post_num, poem_lines, "Has media")
        return


    # remove newlines in cases where each line is followed by a new line
    # unfortunately this mostly doesn't work because of stanza breaks
    if len(poem_lines) > 6:
        even_newlines = True
        odd_newlines = True
        for i in range(3, len(poem_lines)):
            if i % 2 == 0 and len(poem_lines[i].strip()) > 0:
                even_newlines = False
            elif i % 2 != 0 and len(poem_lines[i].strip()) > 0:
                odd_newlines = False

        for i in range(len(poem_lines) - 1, 2, -1):
            if i % 2 == 0 and even_newlines:
                del poem_lines[i]
            elif i % 2 != 0 and odd_newlines:
                del poem_lines[i]

    poem_text_md = "\n".join(poem_lines[1:])  #reconstruct without first line (url)
    poem_text_md = poem_text_md.strip()

    # extract author if possible
    author = re.match(author_regex, poem_text_md)
    if author:
        poem_text_md = poem_text_md.replace(author.group(), "")
        poem_text_md += "\n\n---\n[[" + author.group(1) + "]]"

    # set title - if no title, first non-empty line
    poem_title = post['title']

    if poem_title is None:
        for i in range(1, len(poem_lines)):
            if len(poem_lines[i].strip()) > 0:
                poem_title = textwrap.wrap(poem_lines[i], 40)[0]
                if "/" not in poem_title: #if legal file name
                    break

    if poem_title is not None:
        # format title: title case, remove various extranous charachters
        if poem_title.isupper():
            poem_title = poem_title.title()

        poem_title = poem_title.replace("”", "")
        poem_title = poem_title.replace("“", "")
        poem_title = poem_title.replace("\"", "")
        poem_title = poem_title.replace("«", "")
        poem_title = poem_title.replace("»", "")

        poem_title = poem_title.replace("*", "")

        poem_title = poem_title.strip()

        # if poem_title[-1] == ".":
        #     poem_title = poem_title[:-1]

        #write to "Name of Poem.md"
        f = open("Poems/" + poem_title + ".md", "w")
        f.write(poem_text_md)
        f.close()

        try:
            print(str(post_num) + ": Wrote " + poem_title + " from " + post['reblogged_from_name'])
        except:
            print(str(post_num) + ": Wrote " + poem_title)

    else:
        alert_for_manual_check(post_num, poem_lines, "Poem title is none")


def alert_for_manual_check(post_num, poem_lines, reason):
    f = open("check_posts.md", "a")
    f.write("- " + poem_lines[0] + "\n")
    f.close()

    print(str(post_num) + ": " + reason + ": check " + poem_lines[0] + " manually.")

#https://stackoverflow.com/questions/47311845/print-more-than-20-posts-from-tumblr-api
def get_all_tagged_posts(client, blog):
    offset = 0
    while True:
        result = client.posts(blog, tag = "words", type = 'text', limit = 20, offset = offset, reblog_info = 'true')
        posts = result['posts']

        if not posts:
            return

        for post in posts:
            yield post

        offset += 20
        time.sleep(5) #limit is 300/min

post_num = 1
for post in get_all_tagged_posts(client, blog):
    process_post(post, post_num)
    post_num += 1
