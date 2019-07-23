import base64
import io
from pathlib import Path
import json
import logging
from datetime import datetime
import os
import argparse

from jinja2 import Template
from PIL import Image
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.WARN)

analyser = SentimentIntensityAnalyzer()


def get_args():
    parser = argparse.ArgumentParser(description="Commandline tool for compiling feedback")
    parser.add_argument('-f', '--feedback-dir', required=True, help="Directory where feedback files reside")
    parser.add_argument('-i', '--image-dir', required=True, help="Directory where images reside")
    return parser.parse_args()


def load_feedback_forms(feedback_dir, img_dir):
    form_paths = Path(feedback_dir).glob('**/*.feedback')
    forms = []
    for fp in form_paths:
        with open(fp, 'r') as f:
            try:
                data = json.load(f)
                if data['source'] != "":
                    forms.append(Feedback(data, img_dir))
                else:
                    log.info(f"Skipping {fp} as incomplete")
            except:
                log.debug(f"Failed to load feedback: {fp}", exc_info=True)
                pass
    return forms


def img_to_b64(path):
    img = Image.open(path)
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG")
    b64 = base64.b64encode(buffer.getvalue()).decode('ascii')
    return f"data:image/png;base64,{b64}"


class LinkedIn(object):
    def __init__(self, person_form, img_dir):
        id = person_form['id']
        name = person_form['name']

        if id == "":
            log.info(f"Using default profile image for {name} as there is a missing id")
            self.image = img_to_b64(os.path.join(img_dir, "default.jpg"))
            self.link = ""
        elif not os.path.exists(f"resources/images/people/{id}.jpg"):
            log.warning(
                f"Couldn't find picture for {name}, download from https://www.linkedin.com/in/{id}/ and put into resources/images/people/{id}.jpg")
            self.image = img_to_b64(os.path.join(img_dir, "default.jpg"))
            self.link = f"https://www.linkedin.com/in/{id}/"
        else:
            self.image = img_to_b64(os.path.join(img_dir, f"{id}.jpg"))

            self.link = f"https://www.linkedin.com/in/{id}/"


class Person(object):
    def __init__(self, person_form, img_dir):
        self.linkedin = LinkedIn(person_form, img_dir)
        self.role = person_form['role']
        self.name = person_form['name']


class Feedback(object):
    def __init__(self, feedback_form, img_dir):
        self.reviewee = Person(feedback_form['reviewee'], img_dir)
        self.reviewer = Person(feedback_form['reviewer'], img_dir)
        self.date = feedback_form['date']
        self.comments = feedback_form['comments'].replace("\n","<br /><br />\n")
        self.sentiment = analyser.polarity_scores(feedback_form['comments'])['compound']


if __name__ == "__main__":

    args = get_args()

    with open('resources/templates/index.html', 'r') as f:
        feedback_template = Template(f.read())

    with open('resources/css/feedback.css', 'r') as f:
        css = f.read()

    fb = load_feedback_forms(args.feedback_dir, args.image_dir)
    total_feedbacks = list(Path(args.feedback_dir).glob('**/*.feedback'))
    fb.sort(key=lambda x: (datetime.strptime(x.date, '%d/%m/%Y'), x.sentiment), reverse=True)

    if len(fb) > 0:
        with open('index.html', 'w') as f:
            f.write(feedback_template.render(FeedbackForm=fb, css=css))
        print(f"Completed writing your feedback! {len(fb)} feedback reports included, {len(total_feedbacks)-len(fb)} missing")
    else:
        raise Exception("Could not find any feedback to generate feedback report")
