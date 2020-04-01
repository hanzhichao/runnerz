import yaml

from runnerz.step import StepGroup

def test_step_group():
    with open('/Users/apple/Documents/Projects/Self/PyPi/runnerz/data.yml', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    print(data)
    g = StepGroup(data)
    print(g.name)
    print(g.config)
    print(g.sub_steps)


if __name__ == '__main__':
    test_step_group()