import typer

task = typer.Typer()


@task.command("train")
def do_train(a=123):
    print(a)


@task.command("predict")
def do_predict():
    print(2222)


if __name__ == "__main__":
    task()
