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


def hh_predict_rub_salary(vacancy):
    salary = vacancy['salary']
    predicted_salary = None
    if salary and salary['currency'] == 'RUR':
        s_from = salary['from']
        s_to = salary['to']
        predicted_salary = predict_salary(s_from, s_to)

    return predicted_salary


def sj_predict_rub_salary(vacancy):
    s_from = vacancy['payment_from']
    s_to = vacancy['payment_to']
    return predict_salary(s_from, s_to)


def parse_hh_vacancies(languages):
    base_url = 'https://api.hh.ru/vacancies'
    specialization_code = '1.221'
    area_code = '1'
    headers = {
        'User-Agent': 'curl',
    }
    jobs = {}

    for language in languages:
        params = {
            'specialization': specialization_code,
            'area': area_code,
            'period': '30',
            'text': language,
            'per_page': '100',

        }
        page = 0
        pages_count = 1000
        total_vacancies_processed = 0
        total_average_salary = 0

        while page < pages_count:
            params['page'] = page
            page += 1
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            response = response.json()
            pages_count = response['pages']

            vacancies_found, vacancies_processed, average_salary = parse_hh_language(response)

            total_vacancies_processed += vacancies_processed
            total_average_salary += average_salary

        jobs[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': total_vacancies_processed,
            'average_salary': round(total_average_salary / page)
        }
    return jobs


def parse_hh_language(response):
    vacancies = response['items']
    vacancies_found = response['found']
    vacancies_processed, average_salary = get_average_salary(vacancies, hh_predict_rub_salary)

    return vacancies_found, vacancies_processed, average_salary


def parse_sj_language(response):
    vacancies = response['objects']
    vacancies_found = response['total']
    vacancies_processed, average_salary = get_average_salary(vacancies, sj_predict_rub_salary)

    return vacancies_found, vacancies_processed, average_salary


def parse_sj_vacancies(languages, sj_api_token):
    catalogues_code = '48'
    town_code = '4'
    super_job_url = 'https://api.superjob.ru/2.0/vacancies'
    headers = {
        'X-Api-App-Id': sj_api_token,
    }

    jobs = {}
    for language in languages:

        params = {
            'catalogues': catalogues_code,
            'town': town_code,
            'published_all': 'True',
            'keyword': language,

        }
        page = 0
        pages_count = 1000
        total_vacancies_processed = 0
        total_average_salary = 0

        while page < pages_count:
            params['page'] = page
            page += 1
            response = requests.get(super_job_url, headers=headers, params=params)
            response.raise_for_status()
            response = response.json()

            vacancies_found, vacancies_processed, average_salary = parse_sj_language(response)
            total_vacancies_processed += vacancies_processed
            total_average_salary += average_salary

            pages_count = round(vacancies_found / 20)

        jobs[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': total_vacancies_processed,
            'average_salary': round(total_average_salary / page)
        }
    return jobs


def get_average_salary(vacancies, function):
    vacancies_processed = 0
    all_salaries = 0
    for vacancy in vacancies:
        predicted_salary = function(vacancy)
        if predicted_salary:
            vacancies_processed += 1
            all_salaries += predicted_salary
        average_salary = int(all_salaries / (vacancies_processed if vacancies_processed else 1))

    return vacancies_processed, average_salary


def create_table(jobs, title):
    content = [('Язык программирования', 'Вакансий найдено', 'Вакансий обработано', 'Средняя зарплата'), ]

    for language, statistic in jobs.items():
        jobs_found = statistic['vacancies_found']
        jobs_processed = statistic['vacancies_processed']
        salary = statistic['average_salary']

        content_hh = tuple([language, jobs_found, jobs_processed, salary])
        content.append(content_hh)

    table = AsciiTable(content, title)
    table.justify_columns[len(jobs)] = 'right'
    return table


def main():
    languages = ['Java', 'Python', 'Javascript', 'PHP', 'C++', 'C#', 'C', 'Go', 'Swift']

    hh_title = 'HeadHunter Moscow'
    sj_title = 'SuperJob Moscow'

    sj_api_token = os.getenv['SJ_API_TOKEN']
   
    jobs = parse_hh_vacancies(languages)
    table = create_table(jobs, hh_title)
    print(table.table)
    print()

    jobs = parse_sj_vacancies(languages, sj_api_token)
    table = create_table(jobs, sj_title)
    print(table.table)
    print()


if __name__ == '__main__':
    main()
