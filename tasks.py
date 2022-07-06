from invoke import task


@task
def black(c, docs=False, bytecode=False, extra=""):
    c.run("black . --exclude 'data|stats'")


@task
def tests(c, docs=False, bytecode=False, extra=""):
    c.run("pytest .")
