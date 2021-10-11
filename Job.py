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
    if salary and salary['currency'] == 'RUR':
        s_from = salary['from']
        s_to = salary['to']
        predicted_salary = predict_salary(s_from, s_to)

    return predicted_salary


def predict_rub_salary_for_sj(vacance):
    s_from = vacance['payment_from']
    s_to = vacance['payment_to']
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
        count_pages = 1000
        total_vacancies_processed = 0
        total_average_salary = 0

        while page < count_pages:
            params['page'] = page
            page += 1
            response = requests.get(base_url, headers=headers, params=params)
            response.raise_for_status()
            response = response.json()
            count_pages = response['pages']

            vacancies_found, vacancies_processed, average_salary = parse_language_hh(response)

            total_vacancies_processed += vacancies_processed
            total_average_salary += average_salary

        jobs[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': total_vacancies_processed,
            'average_salary': round(total_average_salary / page)
        }
    return jobs


def parse_language_hh(response):
    vacancies = response['items']
    vacancies_found = response['found']
    vacancies_processed, average_salary = get_average_salary(vacancies, predict_rub_salary_hh)

    return vacancies_found, vacancies_processed, average_salary


def parse_language_sj(response):
    vacancies = response['objects']
    vacancies_found = response['total']
    vacancies_processed, average_salary = get_average_salary(vacancies, predict_rub_salary_for_sj)

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
        count_pages = 1000
        total_vacancies_processed = 0
        total_average_salary = 0

        while page < count_pages:
            params['page'] = page
            page += 1
            response = requests.get(super_job_url, headers=headers, params=params)
            response.raise_for_status()
            response = response.json()

            vacancies_found, vacancies_processed, average_salary = parse_language_sj(response)
            total_vacancies_processed += vacancies_processed
            total_average_salary += average_salary

            count_pages = round(vacancies_found / 20)

        jobs[language] = {
            'vacancies_found': vacancies_found,
            'vacancies_processed': total_vacancies_processed,
            'average_salary': round(total_average_salary / page)
        }
    return jobs


def get_average_salary(vacancies, function):
    vacancies_processed = 0
    all_salaries = 0
    for vacance in vacancies:
        predicted_salary = function(vacance)
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

    title_hh = 'HeadHunter Moscow'
    title_sj = 'SuperJob Moscow'

    sj_api_token = os.getenv['SJ_API_TOKEN']
    jobs = parse_hh_vacancies(languages)
    table = create_table(jobs, title_hh)
    print(table.table)
    print()

    jobs = parse_sj_vacancies(languages, sj_api_token)
    table = create_table(jobs, title_sj)
    print(table.table)
    print()


if __name__ == '__main__':
    main()
