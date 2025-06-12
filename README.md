# 3dom-lod2-generator


### Possible structure:
lod2_reconstruction/
├── main.py
├── requirements.txt
├── README.md
├── config/
│   └── settings.yaml
├── data/
│   └── input_shapefiles/
│   └── output_models/
├── shapefile/
│   └── reader.py
│   └── converter.py
├── modeling/
│   ├── base.py
│   ├── exporter.py
│   ├── blender_ops.py
│   └── roofs/
│       ├── __init__.py
│       ├── gabled.py
│       ├── hip.py
│       ├── flap.py
│       └── pyramid.py
├── cpp_interface/
│   ├── __init__.py
│   ├── run_cgal.py
│   └── helpers.cpp
├── utils/
│   └── geometry.py
│   └── logging_utils.py
└── tests/
    ├── test_reader.py
    ├── test_roofs.py
    └── test_cpp.py
