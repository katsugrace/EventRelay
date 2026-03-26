from config.loader import Config
from args import parse_args


def main():
    args = parse_args()

    config = Config(args.config)
    triggers = config.get_triggers_by_path('/pb/gitlab/pipeline')

    for t in triggers:
        print('Trigger:', t.name)
        print('Message template:', t.message.text)
        print('Notify:', t.notify)


if __name__ == '__main__':
    main()
