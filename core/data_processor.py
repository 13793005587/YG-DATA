import os
import re
import win32com.client
from core.owrk_calculator import owrk_from_template


def parse_doc_contact_angle(file_paths):
    results = []
    word = None

    try:
        try:
            word = win32com.client.DispatchEx("Word.Application")
            print("成功启动 Microsoft Word 后台进程")
        except:
            word = win32com.client.DispatchEx("KWPS.Application")
            print("成功启动 WPS 文字后台进程")
        word.Visible = False
        word.DisplayAlerts = 0
    except Exception as e:
        print(f"无法启动 Office 组件，请确保安装了 Word 或 WPS！错误: {e}")
        return results

    for file_path in file_paths:
        angle = None
        doc = None
        try:
            doc = word.Documents.Open(os.path.abspath(file_path), ReadOnly=True)
            file_name = os.path.basename(file_path)
            print(f"正在后台处理文件: {file_name}")

            for table in doc.Tables:
                if angle is not None:
                    break
                row_count = table.Rows.Count
                col_count = table.Columns.Count
                for i in range(1, row_count + 1):
                    if angle is not None:
                        break
                    row_cells = []
                    for j in range(1, col_count + 1):
                        try:
                            cell_text = table.Cell(i, j).Range.Text.replace('\r', '').replace('\x07', '').replace('\n',
                                                                                                                  '').strip()
                            row_cells.append(cell_text)
                        except:
                            row_cells.append("")

                    # 查找平均角度
                    if "平均角度" in row_cells:
                        for cell in row_cells:
                            try:
                                angle = float(cell)
                                break
                            except ValueError:
                                continue
                        if angle is None:
                            for cell in row_cells:
                                if "平均角度" in cell:
                                    nums = re.findall(r"[-+]?\d*\.\d+|\d+", cell)
                                    if nums:
                                        angle = float(nums[-1])
                                        break
                    # 备用：平均接触角
                    if angle is None and "平均接触角" in row_cells:
                        for cell in row_cells:
                            try:
                                angle = float(cell)
                                break
                            except ValueError:
                                continue

            if angle is not None:
                results.append({'filename': file_name, 'angle': angle})
                print(f"提取成功: {angle}")
            else:
                print(f"未在 {file_name} 中提取到有效角度")

        except Exception as e:
            print(f"读取文件失败 {file_path}: {e}")
        finally:
            if doc:
                try:
                    doc.Close(False)
                except:
                    pass

    try:
        if word:
            word.Quit()
    except:
        pass

    return results


def extract_core_id(filename):
    """
    智能提取文件名中的核心识别码
    优先提取最后一段连续的数字（如 1393-I -> 1393），
    如果没有数字则提取纯字母（如 BJ-I -> BJ）。
    """
    name = filename.replace('.doc', '').replace('.docx', '').strip()
    # 提取所有数字序列
    nums = re.findall(r'\d+', name)
    if nums:
        # 如果文件名有日期（如 20260825_1393），提取最后一个数字，防止提取到日期
        return nums[-1]
    # 没有数字，提取字母组合并去掉常见后缀干扰
    letters = re.findall(r'[a-zA-Z]+', name)
    # 将字母转为小写，并去除常见的“-i”、“water”等后缀干扰
    pure_letters = ''.join(letters).lower().replace('i', '').replace('water', '').replace('diiodo', '')
    return pure_letters


def calculate_surface_energies(water_data, diiodo_data):
    """
    通过提取文件名核心识别码进行智能配对（完全不分先后顺序）
    water_data: [{'filename': '1393.doc', 'angle': 103.085}]
    diiodo_data: [{'filename': '1393-I.doc', 'angle': 73.689}]
    """
    # 建立二碘甲烷的映射字典（通过核心ID查找对应的数据）
    diiodo_map = {}
    for d in diiodo_data:
        core_id = extract_core_id(d['filename'])
        diiodo_map[core_id] = d

    results = []

    # 遍历水滴角，在映射字典中找对应的二碘甲烷
    for w in water_data:
        core_id = extract_core_id(w['filename'])

        if core_id in diiodo_map:
            theta_water = w['angle']
            theta_diiodo = diiodo_map[core_id]['angle']
            # 调用 OWRK 计算公式
            res = owrk_from_template(theta_water, theta_diiodo)

            # 生成结果行
            results.append({
                "文件名": w['filename'],  # 以水滴角文件名作为主显示名
                "水接触角": round(theta_water, 3),
                "二碘甲烷接触角": round(theta_diiodo, 3),
                "极性分量": round(res['gamma_p'], 3),
                "色散分量": round(res['gamma_d'], 3),
                "估值方法": "OWRK",
                "表面能": round(res['gamma_total'], 3)
            })
        else:
            print(f"⚠️ 警告：未找到与 {w['filename']} 匹配的二碘甲烷文件，已跳过。")

    return results


def export_to_excel(data, file_path):
    import pandas as pd
    df = pd.DataFrame(data)
    df.to_excel(file_path, index=False)