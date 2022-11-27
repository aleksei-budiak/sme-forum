FROM python:3.9

COPY requirements.txt /requirements.txt

RUN pip3 install -r /requirements.txt
ENV KVK_SCRAPPING_RESULTS_BUCKET "kvk-scrapping-results"

COPY scraper.py /scraper.py

CMD ["python3","/scraper.py"]