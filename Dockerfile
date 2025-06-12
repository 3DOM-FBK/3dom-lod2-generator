FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Aggiorna e installa dipendenze base
RUN apt-get update && apt-get install -y \
    software-properties-common \
    wget \
    curl \
    git \
    build-essential \
    cmake \
    libboost-all-dev \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    python3-pip \
    libgl1 \
    libxrender1 \
    libxkbcommon-x11-0 \
    libxi6 \
    libxxf86vm1 \
    libxfixes3 \
    libxcursor1 \
    libxrandr2 \
    libxinerama1 \
    libegl1 \
    && rm -rf /var/lib/apt/lists/*

# Imposta Python 3.10 come default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1

# Installa pacchetti Python
# RUN pip install --upgrade pip
# RUN pip install plyfile shapely geopandas

# Installa CGAL 6.0.1 da source
WORKDIR /opt
RUN git clone https://github.com/CGAL/cgal.git && \
    cd cgal && \
    git checkout v6.0.1 && \
    cmake -S . -B build && \
    cmake --build build --target install

# Installa Blender 4.4 Alpha (puoi cambiare URL quando esce la release)
WORKDIR /opt
ENV BLENDER_VERSION=4.4.0
RUN wget https://download.blender.org/release/Blender4.4/blender-${BLENDER_VERSION}-linux-x64.tar.xz && \
    tar -xf blender-${BLENDER_VERSION}-linux-x64.tar.xz && \
    ln -s /opt/blender-${BLENDER_VERSION}-linux-x64/blender /usr/local/bin/blender && \
    rm blender-${BLENDER_VERSION}-linux-x64.tar.xz

RUN /opt/blender-4.4.0-linux-x64/4.4/python/bin/python3.11 -m pip install plyfile shapely geopandas

RUN apt-get update && apt-get install -y libsm6 && rm -rf /var/lib/apt/lists/*

# Imposta working directory
WORKDIR /workspace