# HSML Schema
This repository contains the HSML Schema context, among other codes needed to build and test the interoperability system for Digital Twins. The **HSML (Hyperspatial Modeling Language)** Schema defines a standardized format for spatially-aware data models, enabling interoperability across different platforms and technologies, with an initial primary focus on digital twins.

## Project Goals
- Design a comprehensive schema for representing spatial information following the Spatial Web's standard.
- Facilitate integration with other modeling standards and systems.
- Ensure compatibility with both physical and virtual representations of objects.
- Support a range of use cases, including digital twins, robotics, and real-time simulations.


## Repository Contents
- **`docs/`**: Contains the Documentation that facilitates the understanding and implementation of HSML.
- **`examples/`**: Contains example JSON files for different Entity classes.
- **`hsml-context/`**: Contains the hsml.jsonld context file that defines the classes and properties needed.
- **`presentations/`**: Contains the Weekly Presentations by Alicia Sanjurjo.
- **`scripts/`**: Contains Python scripts developed for the Verification and to test with the Kafka server.
- **`swid_generator/`**: Contains the Python CLI tool used to generate the public & private key pair for the DID:key method.