import subprocess as sp
import os, os.path

import matsim.runtime.git as git
import matsim.runtime.java as java
import matsim.runtime.maven as maven

def configure(context):
    context.stage("matsim.runtime.git")
    context.stage("matsim.runtime.java")
    context.stage("matsim.runtime.maven")

    context.config("pt2matsim_version", "21.1")

def run(context, command, arguments):
    version = context.config("pt2matsim_version")

    # Make sure there is a dependency
    context.stage("matsim.runtime.pt2matsim")

    jar_path = "%s/pt2matsim/target/pt2matsim-%s-shaded.jar" % (
        context.path("matsim.runtime.pt2matsim"), version
    )
    java.run(context, command, arguments, jar_path)

def execute(context):
    version = context.config("pt2matsim_version")

    # Clone repository and checkout version
    git.run(context, [
        "clone", "https://github.com/matsim-org/pt2matsim.git",
        "--branch", "v%s" % version,
        "--single-branch", "pt2matsim",
        "--depth", "1"
    ])

    path = "%s/pt2matsim" % context.path()

    # 🔥 aplica patch automaticamente
    patch_matsim_repository(path)

    # Build pt2matsim
    maven.run(context, ["package", "-DskipTests"], cwd = "%s/pt2matsim" % context.path())
    jar_path = "%s/pt2matsim/target/pt2matsim-%s-shaded.jar" % (context.path(), version)

    # Test pt2matsim
    java.run(context, "org.matsim.pt2matsim.run.CreateDefaultOsmConfig", [
        "test_config.xml"
    ], jar_path)

    assert os.path.exists("%s/test_config.xml" % context.path())

def patch_matsim_repository(path):
    pom_path = os.path.join(path, "pom.xml")

    with open(pom_path, "r") as f:
        content = f.read()

    # Substitui Bintray (HTTP morto) por repo oficial MATSim (HTTPS)
    content = content.replace(
        "http://dl.bintray.com/matsim/matsim",
        "https://repo.matsim.org/repository/matsim"
    )

    with open(pom_path, "w") as f:
        f.write(content)
