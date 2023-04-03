import requests
import logging
from bs4 import BeautifulSoup
from typing import List
import time

import constants
from data.dao import DAO
from helper import only_business_time
from telegram_channels import channels, formatter


class Job:
    def __init__(self):
        self.dao = DAO.get_instance()

    # @only_business_time
    def execute(self):
        """
        Executes the job scraper. Retrieves jobs, parses them, saves them to the database,
        and sends alerts for new job listings.
        """

        logging.info("Fetch jobs...")

        try:
            jobs = self._get_jobs()

            if jobs == None:  # couldn't get jobs
                return

            job_count = 0

            if not self.dao.created:
                # in the first execution, save the entire database

                job_history = self._parse_jobs(jobs)

                for job in job_history:
                    self._insert_db(job)
                    job_count += 1

                self.dao.created = True
                logging.info("Database created and data was loaded successfully.")

            else:
                # after being run for the first time, it will start sending alerts

                job_history = self._parse_jobs(jobs, constants.LIMIT_JOBS_PER_FETCH)

                for job in job_history:

                    # if the job is already registered, do not alert
                    if not self._exists_db(job):
                        self._insert_db(job)
                        job_count += 1

                        self._send_job_alert(job, True)

            return logging.info(f"{job_count} jobs inserted.")

        except Exception as e:
            logging.exception(e)
            return

    def _get_jobs(self) -> str:
        """
        Retrieves job listings HTML from the website.

        Returns:
            str: Job listings HTML.
        """

        # TODO: helper.make_request

        # TODO: helper.read_file
        # with open("tst.html", "r") as f:
        #     return f.read()

        for attempt in range(constants.MAX_ATTEMPTS):

            with requests.Session() as ses:
                ses.post(constants.LOGIN_URL, data=constants.USUARIO)
                jobs = ses.get(constants.VAGAS_URL, data={"IdCurso": 4})

                if jobs.ok:
                    return jobs.text
                else:
                    logging.warn(
                        f"Attempt {attempt+1} failed (get_jobs() - code {jobs.status_code})"
                    )
                    time.sleep(constants.INTERVAL_MINUTES)

        else:
            logging.critical("Problems found when trying to get jobs")
            return None

    def _parse_jobs(self, jobs: str, limit: int = None) -> List:
        """
        Parses job listings HTML to extract relevant information.

        Args:
            jobs (str): Job listings HTML.
            limit (int, optional): Maximum number of jobs to retrieve. Defaults to None.

        Returns:
            List: List of dictionaries containing job details.
        """

        parsed_html = BeautifulSoup(jobs, "html.parser")

        _jobs_list = []
        _job = []
        _FILTER = ["Email:"]

        for row in parsed_html.find_all("div", class_="row"):

            if any(forbidden_row in row.text for forbidden_row in _FILTER):
                continue

            for inner_div in row.find_all("div"):

                if inner_div.text.replace("\n", "").strip():

                    for strong in inner_div.find_all("strong"):
                        strong.decompose()

                    _job.append(inner_div.text.replace("\n", "").strip())

            # TODO: validate if all fields of a job are filled,
            # else fill the unfilled with emtpy strings
            #
            # if all(_checks.values()):
            #     print("all filled")

            if len(_job) == 9:  # a single job requires 9 elements of information
                _jobs_list.append(_job.copy())
                _job.clear()

        final_result = self._format_jobs(
            _jobs_list if limit is not None else _jobs_list[:limit]
        )

        return final_result

    def _format_jobs(self, jobs: List) -> list[dict]:
        """
        Formats job details by transforming it in readable
        dictionaries and removing unnecessary characters.

        Args:
            json (list): Dictionary containing job details.
        """

        KEYS = constants.JOB_FIELDS.keys()

        _formatted_results = []

        for job in jobs:
            values = [detail.replace("\n", "").strip() for detail in job]
            _formatted_results.append(dict(zip(KEYS, values)))

        return _formatted_results

    def _send_job_alert(self, job: dict, insert_emojis: bool = False):
        """
        Sends an alert for a new job listing.

        Args:
            job (dict): Dictionary containing job details.
            insert_emojis (bool): option to add emojis to the message
        """

        message = "Nova vaga cadastrada:\n\n"

        if insert_emojis:
            formatter.emojis(message, job)
        else:
            message += "\n".join(
                [f"{key}: {value.capitalize()}"]
                for key, value in job.items()
                if not value
            )

        channels.send(constants.VAGAS_CHAT_ID, message)

    def _exists_db(self, job) -> bool:
        # Checks if a job listing already exists in the database.

        search = self.dao.jobs.search(self.dao.query.fragment(job))
        return len(search) > 0

    def _insert_db(self, job) -> None:
        self.dao.jobs.insert(job)

    def _update_db(self, job) -> None:
        self.dao.jobs.update(job)

    def _delete_db(self, job) -> None:
        self.dao.jobs.remove(job)
