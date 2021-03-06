import os
import logging
from dataloop_services.dataloop_converter import convert_dataloop_to_coco
import dtlpy as dl
import shutil

logger = logging.getLogger(__name__)
data_format = 'dataloop'


def get_dataset_obj(dataloop_configs):
    try:
        project_id = dataloop_configs['project_id']
        dataset_id = dataloop_configs['dataset_id']
        project = dl.projects.get(project_id=project_id)
        dataset_obj = project.datasets.get(dataset_id=dataset_id)
    except:
        project_name = dataloop_configs['project']
        dataset_name = dataloop_configs['dataset']
        project = dl.projects.get(project_name=project_name)
        dataset_obj = project.datasets.get(dataset_name)
    return dataset_obj


def maybe_download_data(dataset_obj, query):
    # check if data is downloaded if not then download
    filters = dl.Filters()
    filters.custom_filter = query
    logger.info('query: ' + str(query))
    logger.info('filters: ' + str(filters.prepare()))

    parent_dir = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
    path_to_put_data = os.path.join(parent_dir, 'data')
    if not os.path.exists(path_to_put_data):
        os.mkdir(path_to_put_data)

    if data_format == 'dataloop':
        dataset_name = dataset_obj.name
        path_to_dataset = os.path.join(path_to_put_data, dataset_name)

        if os.path.exists(path_to_dataset):
            logger.info(dataset_name + ' already exists, no need to download')
            if not os.path.exists(os.path.join(path_to_dataset,'annotations')):
                convert_dataloop_to_coco(path_to_data=path_to_dataset, name='train', split_val=True)
        else:
            os.mkdir(path_to_dataset)
            dataset_obj.items.download(local_path=path_to_dataset, filters=filters)
            dataset_obj.download_annotations(local_path=path_to_dataset, filters=filters)

            images_folder = os.path.join(path_to_dataset, 'items')
            json_folder = os.path.join(path_to_dataset, 'json')
            # move to imgs and annotations to fixed format
            for path, su1bdirs, files in os.walk(images_folder):
                for name in files:
                    filename, ext = os.path.splitext(name)
                    if ext.lower() not in ['.jpg', '.jpeg', '.png']:
                        continue
                    img_path = os.path.join(path, name)
                    new_img_path = os.path.join(images_folder, name)
                    json_path = os.path.join(path.replace(images_folder, json_folder), filename + '.json')
                    new_json_path = os.path.join(json_folder, filename + '.json')
                    os.rename(img_path, new_img_path)
                    os.rename(json_path, new_json_path)
            # delete dirs leave images and jsons
            for stuff in os.listdir(images_folder):
                im_path = os.path.join(images_folder, stuff)
                if os.path.isdir(im_path):
                    shutil.rmtree(im_path, ignore_errors=True)
            for stuff in os.listdir(json_folder):
                js_path = os.path.join(json_folder, stuff)
                if os.path.isdir(js_path):
                    shutil.rmtree(js_path, ignore_errors=True)

            toy_dataset = False
            if not toy_dataset:
                convert_dataloop_to_coco(path_to_data=path_to_dataset, name='train', split_val=True)
            else:
                convert_dataloop_to_coco(path_to_data=path_to_dataset, name='train', split_val=False)
                convert_dataloop_to_coco(path_to_data=path_to_dataset, name='val', split_val=False)

    else:
        name = dataset_obj.directory_tree.dir_names[-2].strip('/')
        if os.path.exists(os.path.join(path_to_put_data, name)):
            logger.info(name + ' already exists, no need to download')
        else:
            dataset_obj.items.download(local_path=path_to_put_data, to_items_folder=False)

        logger.info('downloaded dataset to ' + path_to_put_data)
