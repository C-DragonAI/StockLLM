import typer

task = typer.Typer()


@task.command("train")
def do_train():
    print("In do_train()")


@task.command("predict")
def do_predict():
    print("In do_predict()")


if __name__ == "__main__":
    task()
