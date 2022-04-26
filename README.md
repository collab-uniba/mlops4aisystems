# Replication package for the EMSE 2022 paper 

This is the replication package of the EMSE 2022 NIER track paper "A Preliminary Analysis of CI/CD for AI-enabled systems".

## Setup

Before running the scripts contained in this repository, you first need to create an `env.ini` file in the project root directory and populate it with the following entries:

```ini
[GITHUB]
TOKEN_LIST = [
        "faketoken1",
        "faketoken2",
        "faketoken3",
        "faketoken4",
        "faketoken5",
    ]

[PATHS]
DATA_DIR = path/to/data/dir
LOGS_DIR = path/to/logs/dir
DUMPS_DIR = path/to/dumps/dir
```

To install the dependencies, open a Poetry shell session and run:

```shell
poetry shell
make install
```

## Execution

Within an active Poetry shell session, run the scripts as follows:

```shell
python actions4DS/main.py
python actions4DS/analyze_workflows.py
```

## List of CML repositories
| Repository                                                                          | Purpose                                               |  Included Y/N |
|-------------------------------------------------------------------------------------|-------------------------------------------------------|---------------|
| https://github.com/0x2b3bfa0/test                                                   | Empty                                                 | No            |
| https://github.com/augustovictor/github-actions-lab                                 | Empty                                                 | No            |
| https://github.com/dacbd/err                                                        | No ML model                                           | No            |
| https://github.com/KomorebiTso/My-repository1                                       | No ML model                                           | No            |
| https://github.com/mpolch/github                                                    | Empty                                                 | No            |
| https://github.com/radistoubalidis/DVC_Tutorial                                     | CML tutorial implementation                           | No            |
| https://github.com/2796gaurav/automate                                              | Test-drive                                            | Yes           |
| https://github.com/akdsingh/cml                                                     | Test-drive                                            | Yes           |
| https://github.com/akdsingh/cml_data                                                | Test-drive                                            | Yes           |
| https://github.com/amitvkulkarni/Bring-DevOps-to-Machine-Learning-with-CML          | Educational                                           | Yes           |
| https://github.com/AmonKi/abtest-mlops                                              | PR code submitted to Smart Ad server                  | Yes           |
| https://github.com/ArilessTir/MLOPS_wine                                            | Test-drive                                            | Yes           |
| https://github.com/AscendNTNU/perception_testing_21                                 | Drone software testing                                | Yes           |
| https://github.com/CasualModel/CancerCausality                                      | Test-drive                                            | Yes           |
| https://github.com/cheesama/morphine                                                | Library extension for entity classification in Korean | Yes           |
| https://github.com/daheek9/github-actions-cml-2                                     | Test-drive                                            | Yes           |
| https://github.com/DavidGOrtega/terraform-provider-tpitest                          | Test-drive                                            | Yes           |
| https://github.com/drforester/mlops_666                                             | Test-drive                                            | Yes           |
| https://github.com/faithccd/github-actions-cml                                      | Test-drive                                            | Yes           |
| https://github.com/hacheemaster/wine                                                | Test-drive                                            | Yes           |
| https://github.com/hurshd0/train_ml_with_github_actions                             | Test-drive                                            | Yes           |
| https://github.com/ibrahimkaratas88/cml_base_case                                   | Test-drive                                            | Yes           |
| https://github.com/ibrahimkaratas88/cml_cloud_try                                   | Test-drive                                            | Yes           |
| https://github.com/j-cunanan/git-action-examples                                    | Test-drive                                            | Yes           |
| https://github.com/luelhagos/abtest-mlops                                           | Test-drive                                            | Yes           |
| https://github.com/luelhagos/Pharmaceutical-Sales-prediction-across-multiple-stores | Test-drive                                            | Yes           |
| https://github.com/Maelaf/abtest-mlops                                              | Test-drive                                            | Yes           |
| https://github.com/MaSobkowiak/IUM                                                  | Test-drive                                            | Yes           |
| https://github.com/mozartofmath/AmharicSpeechToText                                 | Speech-to-text model                                  | Yes           |
| https://github.com/RakeshKumar045/MLOPS-Github-CI-CD-ML-Model                       | Test-drive                                            | Yes           |
| https://github.com/SungminKo-smko/github-actions-cml                                | Test-drive                                            | Yes           |
| https://github.com/Theehawau/Sales-Prediction                                       | Test-drive                                            | Yes           |
| https://github.com/tue-5ARA0/mlops-demo-live                                        | Educational                                           | Yes           |
| https://github.com/YannickLecroart/pmr                                              | Test-drive                                            | Yes           |
| https://github.com/YannickLecroart/pmr_cml_pipeline                                 | Test-drive                                            | Yes           |
| https://github.com/YannickLecroart/pmr_dvc_demo                                     | Test-drive                                            | Yes           |
