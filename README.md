
Dev env

```bash
python -m venv ~/.venvs/rulm-sbs2
source ~/.venvs/rulm-sbs2/bin/activate

pip install \
  tqdm \
  pandas pyarrow \
  matplotlib \
  aiohttp \
  openai \
  label-studio-sdk

pip install ipywidgets ipykernel
python -m ipykernel install --user --name rulm-sbs2
```

Create/delete Yagpt service user

```bash

yc iam service-accounts create rulm-sbs2 --folder-name default
yc resource-manager folder add-access-binding default \
    --role ai.languageModels.user \
    --service-account-name rulm-sbs2 \
    --folder-name default
yc resource-manager folder list-access-bindings --name default

yc iam service-accounts delete rulm-sbs2 --folder-name default
```
