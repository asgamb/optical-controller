# Copyright 2022-2023 ETSI TeraFlowSDN - TFS OSG (https://tfs.etsi.org/)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM python:3.9-slim

# Install dependencies
RUN apt-get --yes --quiet --quiet update && \
    apt-get --yes --quiet --quiet install wget g++ && \
    rm -rf /var/lib/apt/lists/*

# Set Python to show logs as they occur
ENV PYTHONUNBUFFERED=0

# Download the gRPC health probe
# RUN GRPC_HEALTH_PROBE_VERSION=v0.2.0 && \
#     wget -qO/bin/grpc_health_probe https://github.com/grpc-ecosystem/grpc-health-probe/releases/download/${GRPC_HEALTH_PROBE_VERSION}/grpc_health_probe-linux-amd64 && \
#     chmod +x /bin/grpc_health_probe




# Get generic Python packages
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --upgrade setuptools wheel
RUN python3 -m pip install --upgrade pip-tools



COPY common_requirements.in common_requirements.in
RUN pip-compile --quiet --output-file=common_requirements.txt common_requirements.in
RUN python3 -m pip install -r common_requirements.txt

RUN mkdir -p /var/teraflow/opticalcontroller

WORKDIR /var/teraflow/opticalcontroller/common
COPY src/common/. ./
RUN rm -rf proto


# Create proto sub-folder, copy .proto files, and generate Python code
RUN mkdir -p /var/teraflow/opticalcontroller/common/proto
WORKDIR /var/teraflow/opticalcontroller/common/proto
RUN touch __init__.py
COPY proto/*.proto ./
RUN python3 -m grpc_tools.protoc -I=. --python_out=. --grpc_python_out=. *.proto
RUN rm *.proto
RUN find . -type f -exec sed -i -E 's/(import\ .*)_pb2/from . \1_pb2/g' {} \;

# Create component sub-folder, get specific Python packages



WORKDIR /var/teraflow/opticalcontroller
COPY src/opticalcontroller/requirements.in requirements.in
RUN pip-compile --quiet --output-file=requirements.txt requirements.in
RUN python3 -m pip install -r requirements.txt

# Add component files into working directory
WORKDIR /var/teraflow/

COPY src/context/. context/

COPY src/opticalcontroller/. opticalcontroller/
COPY src/context/. opticalcontroller/context/

# Start the service
WORKDIR /var/teraflow/opticalcontroller
ENTRYPOINT ["python", "OpticalController.py"]
