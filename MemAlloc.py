from tkinter import *
import tkinter.ttk as ttk

# 进程计数
process_count = 0

allocated_list = {}

root = Tk()
root.title("内存管理模拟")

# 初始化内存块链表
free_list = [(0, 640)]

# 显示内存布局的Canvas
memory_canvas = None

# 首次适应和最佳适应的算法选择
algo_var = StringVar()
algo_var.set('首次适应')

# 进程块大小输入
size_entry = None

# 表格显示内存块链表
table = None
allocated_table = None


def init_ui():
    global memory_canvas, size_entry, table, algo_var, allocated_table

    # 选择算法按钮组
    algo_frame = Frame(root)
    algos = ['首次适应', '最佳适应']
    for algo in algos:
        Radiobutton(algo_frame, text=algo, variable=algo_var, value=algo).pack(side=LEFT)
    algo_frame.pack()

    # 输入进程块大小的entry和提交按钮
    size_frame = Frame(root)
    size_entry = Entry(size_frame)
    size_entry.pack(side=LEFT, padx=5)
    Button(size_frame, text='提交', command=alloc_memory).pack(side=LEFT)
    Button(size_frame, text='清空', command=clear_all).pack(side=LEFT)
    size_frame.pack(pady=5)

    # 显示内存布局的Canvas
    memory_canvas = Canvas(root, width=640, height=100, bg='white')
    memory_canvas.pack()

    # 创建用于存放 allocated_table 和 table 的框架，并将其添加到 root 中
    tables_frame = ttk.Frame(root)
    tables_frame.pack(pady=10)

    # 创建用于存放 allocated_table 的框架，并将其添加到 tables_frame 中
    allocated_table_frame = ttk.Frame(tables_frame)
    allocated_table_frame.pack(side='left', padx=10)

    # 在 allocated_table 上方添加标题
    allocated_table_label = ttk.Label(allocated_table_frame, text="已分配内存块")
    allocated_table_label.pack(pady=5)

    # 显示已分配内存块列表的表格
    allocated_table = ttk.Treeview(allocated_table_frame, columns=['process', 'start', 'end'], show='headings')
    allocated_table.column('process', width=100)
    allocated_table.column('start', width=100)
    allocated_table.column('end', width=100)
    allocated_table.heading('process', text='进程号')
    allocated_table.heading('start', text='起始地址')
    allocated_table.heading('end', text='结束地址')
    allocated_table.pack()

    # 创建用于存放 table 的框架，并将其添加到 tables_frame 中
    table_frame = ttk.Frame(tables_frame)
    table_frame.pack(side='left', padx=10)

    # 在 table 上方添加标题
    table_label = ttk.Label(table_frame, text="空闲内存块")
    table_label.pack(pady=5)

    # 显示内存块链表的表格
    table = ttk.Treeview(table_frame, columns=['start', 'end'], show='headings')
    table.column('start', width=100)
    table.column('end', width=100)
    table.heading('start', text='起始地址')
    table.heading('end', text='结束地址')
    table.pack()

    # 退出按钮
    Button(root, text='退出', command=root.quit).pack(pady=10)  # 增加留白

    root.mainloop()


# 分配内存函数
def alloc_memory():
    global memory_canvas, free_list, table, algo_var, process_count, allocated_list, allocated_table

    # 获取输入的进程块大小
    size = int(size_entry.get())

    # 检查是否有足够的空闲内存来分配给新进程
    while not any(end - start >= size for start, end in free_list) and allocated_list:
        # 根据FIFO策略释放最早分配的进程
        released_process = min(allocated_list.keys())
        free_list = release_process(released_process)

    # 根据选择的算法分配内存块
    if algo_var.get() == '首次适应':
        start_addr = first_fit(free_list, size)
    else:
        start_addr = best_fit(free_list, size)

    # 更新内存布局和内存块链表
    if start_addr != -1:
        process_count += 1
        free_list = allocate(free_list, start_addr, size)
        allocated_list[process_count] = (start_addr, start_addr + size)
        display_memory(memory_canvas)
        display_table(table, free_list)
        display_allocated_table(allocated_table, allocated_list)

    # 清空输入框的内容
    size_entry.delete(0, 'end')


# 释放进程并更新内存块链表
def release_process(process_num):
    global free_list, allocated_list, allocated_table

    start, end = allocated_list[process_num]
    free_list.append((start, end))
    free_list.sort(key=lambda x: x[0])

    # 合并相邻的空闲内存块
    new_free_list = []
    prev_start, prev_end = free_list[0]
    for start, end in free_list[1:]:
        if prev_end == start:
            prev_end = end
        else:
            new_free_list.append((prev_start, prev_end))
            prev_start, prev_end = start, end

    new_free_list.append((prev_start, prev_end))
    free_list = new_free_list

    # 从已分配内存列表中删除释放的进程
    del allocated_list[process_num]

    # 更新内存布局和内存块链表表格
    display_memory(memory_canvas)
    display_table(table, free_list)
    display_allocated_table(allocated_table, allocated_list)

    return free_list


# 首次适应算法
def first_fit(free_list, size):
    for start, end in free_list:
        if end - start >= size:
            return start
    return -1


# 最佳适应算法
def best_fit(free_list, size):
    best_idx, best_size = 0, float('inf')  # 将 best_size 初始化为无穷大
    for i, (start, end) in enumerate(free_list):
        if end - start >= size and end - start < best_size:
            best_idx, best_size = i, end - start
    if best_size != float('inf'):  # 检查是否找到合适的内存块
        return free_list[best_idx][0]
    else:
        return -1


# 分配内存块并更新内存块链表
def allocate(free_list, start_addr, size):
    new_free_list = []
    for start, end in free_list:
        if start_addr == start and end - start > size:
            new_free_list.append((start + size, end))
        elif start_addr == start and end - start == size:
            pass
        elif start < start_addr < end:
            new_free_list.append((start, start_addr))
            if end - (start_addr + size) > 0:
                new_free_list.append((start_addr + size, end))
        else:
            new_free_list.append((start, end))

    return new_free_list


# 在画布上显示内存布局
def display_memory(memory_canvas):
    global free_list, allocated_list

    # 清空画布
    memory_canvas.delete('all')

    # 画出总的内存块
    memory_canvas.create_rectangle(0, 0, 640, 100, fill='white', outline='black')

    # 画出各个进程块和空闲内存块
    for process_num, (start, end) in allocated_list.items():
        memory_canvas.create_rectangle(start, 0, end, 100, fill='lightskyblue', outline='black')
        memory_canvas.create_text((start + end) / 2, 50, text="P{}".format(process_num))

    for start, end in free_list:
        memory_canvas.create_rectangle(start, 0, end, 100, fill='gray', outline='black')


def display_allocated_table(allocated_table, allocated_list):
    allocated_table.delete(*allocated_table.get_children())

    for process_num, (start, end) in allocated_list.items():
        allocated_table.insert('', 'end', values=(process_num, start, end - 1))


# 更新并显示内存块链表
def display_table(table, free_list):
    table.delete(*table.get_children())

    for start, end in free_list:
        table.insert('', 'end', values=(start, end - 1))


# 清空所有内存按钮的回调函数
def clear_all():
    global process_count, free_list, allocated_list
    process_count = 0

    # 清空内存布局画布
    memory_canvas.delete('all')

    # 重置内存块链表为空
    free_list = [(0, 640)]

    # 重置已分配内存列表
    allocated_list = {}

    # 清空表格
    table.delete(*table.get_children())
    allocated_table.delete(*allocated_table.get_children())


if __name__ == '__main__':
    init_ui()
