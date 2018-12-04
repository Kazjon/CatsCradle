
# CatsCradle
Codebase for the "Cat's Cradle" art project.

To use face and gender detection:

1. Download the file `pretrained_checkpoints.zip` from [here](https://drive.google.com/file/d/1mL-JefASON9fWjsk_ANylonqdC_Hngud/view?usp=sharing).
2. Unzip it and place the resulting folder, `pretrained_checkpoints/` within `age_and_gender_detection/`
3. Download the file `face_detection.zip` from [here](https://drive.google.com/file/d/1pRgEsuPDk9ovr41gzCsWyYQRb401YLaT/view?usp=sharing).
4. Unzip it and place the resulting folder, `face_detection/` within the parent folder of the repository.
5. The final folder structure should look like:

`parent_dir`
├── files...
├── `age_and_gender_detection`
    ├── `pretrained_checkpoints`
      └── ...
├── `face_detection`
      └── ...
