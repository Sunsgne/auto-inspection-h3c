import logging
import os
import zipfile


logger = logging.getLogger('linux_collector')


def file_zip(zip_file_name: str, file_names: list, policies_job):
    for fn in file_names:
        with zipfile.ZipFile(zip_file_name, mode='a', compression=zipfile.ZIP_DEFLATED) as zf:
            parent_path, name = os.path.split(fn)
            # zipfile 内置提供的将文件压缩存储在.zip文件中， arcname即zip文件中存入文件的名称
            # 给予的归档名为 arcname (默认情况下将与 filename 一致，但是不带驱动器盘符并会移除开头的路径分隔符)
            zf.write(fn, arcname=name)
            zf.close()
            logger.info('zip file %s to %s success!' % (name, zip_file_name))
            # 判断文件是否存在
            if os.path.exists(fn):
                os.remove(fn)
                logger.info('delete %s success!' % fn)
    # 追加完成后获取文件大小，每次追加完成后更新数据
    path_size = os.path.getsize(policies_job.file_path)/1024
    policies_job.size = '%.2f' % path_size
    policies_job.save()
