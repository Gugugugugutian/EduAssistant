from typing import Dict, List
from datetime import datetime
from app.react.tools_register import register_as_tool
from app.utils.logging import logger
from app.models.course import Course

def generate_teaching_outline(course_id: int, week: int, objectives: List[str]) -> str:
    """生成备课提纲
    
    Args:
        course_id (int): 课程ID
        week (int): 教学周次
        objectives (List[str]): 教学目标列表
        
    Returns:
        str: 生成的备课提纲
    """
    course = Course.get_by_id(course_id)
    if not course:
        return "错误：课程不存在"
    
    outline = f"【{course.name}】第{week}周备课提纲\n\n"
    outline += "一、教学目标：\n"
    for i, obj in enumerate(objectives, 1):
        outline += f"{i}. {obj}\n"
    
    outline += "\n二、教学内容：\n"
    outline += "1. 知识点讲解\n2. 课堂练习\n3. 互动讨论\n"
    
    outline += "\n三、教学资源：\n"
    outline += "- PPT课件\n- 教学视频\n- 练习题\n"
    
    outline += "\n四、课后作业：\n"
    outline += "- 阅读材料\n- 实践任务\n"
    
    return outline

def generate_teaching_summary(course_id: int, week: int, 
                           achievements: List[str], issues: List[str]) -> str:
    """生成教学总结
    
    Args:
        course_id (int): 课程ID
        week (int): 教学周次
        achievements (List[str]): 教学成果
        issues (List[str]): 存在问题
        
    Returns:
        str: 生成的教学总结
    """
    course = Course.get_by_id(course_id)
    if not course:
        return "错误：课程不存在"
    
    summary = f"【{course.name}】第{week}周教学总结\n\n"
    summary += "一、教学成果：\n"
    for i, ach in enumerate(achievements, 1):
        summary += f"{i}. {ach}\n"
    
    summary += "\n二、存在问题：\n"
    for i, issue in enumerate(issues, 1):
        summary += f"{i}. {issue}\n"
    
    summary += "\n三、改进措施：\n"
    summary += "1. 调整教学方法\n2. 增加辅导时间\n3. 优化教学资源\n"
    
    summary += f"\n总结时间：{datetime.now().strftime('%Y-%m-%d')}"
    return summary