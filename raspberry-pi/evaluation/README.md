# Evaluation Data

## Directory structure

enrollment/{name}/   ? N photos per person to build the face DB (e.g. 5-10 JPGs)
probes/{name}/       ? M DIFFERENT photos of the same people to test against (e.g. 3-5 JPGs)
impostors/           ? Unknown people (LFW). Populate with:
                       python scripts/evaluate_offline.py --download-lfw evaluation/impostors/ --max-people 20 --min-photos 3

## Usage

# Build both databases (with and without augmentation)
python database/build_database.py --data_dir evaluation/enrollment --output_dir evaluation/db_noaug
python database/build_database.py --data_dir evaluation/enrollment --output_dir evaluation/db_aug --augment

# Run evaluation and export to Excel
python scripts/evaluate_recognition.py
