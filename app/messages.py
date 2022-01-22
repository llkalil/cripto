from termcolor import colored


def warning_msg(message):
    print(colored('[Message]: ' + message, 'yellow'))


def error_msg(message):
    print(colored('[Error]: ' + message, 'red'))


def success_msg(message):
    print(colored('[Success]: ' + message, 'green'))

