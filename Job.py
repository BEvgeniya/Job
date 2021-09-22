import os

import requests
from terminaltables import AsciiTable


def predict_salary(s_from, s_to):
    predicted_salary = None
    if s_from and s_to:
        predicted_salary = int((s_from + s_to) / 2)
    elif s_from:
        predicted_salary = int(s_from * 1.2)
    elif s_to:
        predicted_salary = int(s_to * 0.8)
    return predicted_salary


def predict_rub_salary_hh(vacance):
    salary = vacance['salary']
    predicted_salary = None
    if salary:
        s_from = salary['from']
        s_to = salary['to']
        if salary['currency'] == 'RUR':
            predicted_salary = predict_salary(s_from, s_to)

    return predicted_salary


def predict_rub_salary_for_sj(vacance):
    s_from = vacance['payment_from']
    s_to = vacance['payment_to']
    if s_from == 0:
        s_from = None
    if s_to == 0:
        s_to = None
    return predict_salary(s_from, s_to)


def parse_hh_vacancies(jobs):
    base_url = 'https://api.hh.ru/vacancies'
    headers = {
        'User-Agent': 'curl',
    }

    languages = list(jobs.keys())

    for language in languages:
        params = {
            'specialization': '1.221',
            'area': '1',
            'period': '30',
            'text': language,
            'per_page': '100',
            'page': '0'

        }
        response = requests.get(base_url, headers=headers, params=params)
        response.raise_for_status()
        vacancies = response.json()['items']

        vacancies_found = response.json()['found']

        count_pages = response.json()['pages']

        all_salaries = 0
        vacancies_processed = 1

        for page in range(count_pages):
            params['page'] = page
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            vacancies = response.json()['items']

            for vacance in vacancies:
                predicted_salary = predict_rub_salary_hh(vacance)
                if predicted_salary:
                    vacancies_processed += 1
                    all_salaries += predicted_salary
            average_salary = int(all_salaries / vacancies_processed)

        jobs[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed-1,
            'average_salary': average_salary
        }
    return jobs


def parse_sj_vacancies(jobs):
    languages = list(jobs.keys())
    sj_api_token = os.getenv['SJ_API_TOKEN']
    for language in languages:

        super_job_url = 'https://api.superjob.ru/2.0/vacancies'
        headers = {
            'X-Api-App-Id': sj_api_token,
        }

        params = {
            'catalogues': '48',
            'town': '4',
            'published_all': 'True',
            'keyword': language,
            'page': '0'

        }

        response = requests.get(super_job_url, headers=headers, params=params)
        response.raise_for_status()
        vacancies_found = response.json()['total']
        count_pages = round(response.json()['total'] / 20)

        all_salaries = 0
        vacancies_processed = 1

        for page in range(count_pages):
            params['page'] = page
            response = requests.get(super_job_url, headers=headers, params=params)
            response.raise_for_status()

            vacancies = response.json()['objects']

            for vacance in vacancies:
                predicted_salary = predict_rub_salary_for_sj(vacance)
                if predicted_salary:
                    vacancies_processed += 1
                    all_salaries += predicted_salary
                average_salary = int(all_salaries / vacancies_processed)

        jobs[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': vacancies_processed - 1,
            'average_salary': average_salary
        }
    return jobs


def create_table(jobs, title):
    table_data = [('Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'), ]
    languages = list(jobs.keys())
    for language in languages:
        jobs_found = jobs[language]['vacancies_found']
        jobs_processed = jobs[language]['vacancies_processed']
        salary = jobs[language]['average_salary']

        content_hh = tuple([language, jobs_found, jobs_processed, salary])
        table_data.append(content_hh)

    table = AsciiTable(table_data, title)
    table.justify_columns[len(languages)] = 'right'
    print(table.table)
    print()


def main():
    jobs = {
        'Java': '',
        'Python': '',
        'Javascript': '',
        'PHP': '',
        'C++': '',
        'C#': '',
        'C': '',
        'Go': '',
        'Swift': ''
    }
    title_hh = 'HeadHunter Moscow'
    title_sj = 'SuperJob Moscow'

    jobs = parse_hh_vacancies(jobs)
    create_table(jobs, title_hh)

    jobs = parse_sj_vacancies(jobs)
    create_table(jobs, title_sj)


if __name__ == '__main__':
    main()
