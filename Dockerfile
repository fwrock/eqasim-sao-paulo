FROM mambaorg/micromamba:1.5.0

USER root

WORKDIR /workspace

RUN apt update && \
    apt install -y wget curl git tar libfreetype6 libfreetype6 libfontconfig1 fonts-dejavu && \
    rm -rf /var/lib/apt/lists/*

# 2. Download and install JDK 25 manually
RUN curl -fsSL https://download.oracle.com/java/25/latest/jdk-25_linux-x64_bin.tar.gz | tar -xz -C /opt && \
    mv /opt/jdk-25* /opt/jdk-25

# 3. Download and install Maven manually
RUN curl -fsSL https://dlcdn.apache.org/maven/maven-3/3.9.14/binaries/apache-maven-3.9.14-bin.tar.gz | tar -xz -C /opt && \
    mv /opt/apache-maven-3.9.14 /opt/maven

# 4. Set Java and Maven environment variables for all users
ENV JAVA_HOME=/opt/jdk-25
ENV M2_HOME=/opt/maven
ENV PATH="${JAVA_HOME}/bin:${M2_HOME}/bin:${PATH}"

USER $MAMBA_USER

RUN micromamba create -y -n eqasim \
    -c conda-forge \
    python=3.7 \
    geopandas \
    fiona \
    shapely \
    gdal \
    libtiff \
    pyproj \
    rtree \
    tqdm \
    pandas \
    numpy \
    scipy \
    scikit-learn \
    numba \
    matplotlib \
    pytables \
    xlrd \
    palettable \
    pip \
    && micromamba clean --all --yes

ENV PATH=/opt/conda/envs/eqasim/bin:$PATH
ENV PROJ_LIB=/opt/conda/envs/eqasim/share/proj
ENV PYTHONPATH=/workspace

RUN pip install \
    synpp==1.2.2 \
    pyreadstat==0.3.4 \
    simpledbf==0.2.6 \
    osmium==3.0.0 \
    gtfsmerger==0.1.6

ENTRYPOINT ["python3", "-m", "synpp"]
