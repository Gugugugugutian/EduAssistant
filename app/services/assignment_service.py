from datetime import datetime
from app.models.assignment import Assignment, StudentAssignment
from app.models.course import Course, StudentCourse

class AssignmentService:
    """作业服务类，处理作业管理和学生作业提交。
    
    该服务提供作业相关的所有功能，包括作业创建、分发、提交、
    评分等功能。
    """
    
    def create_assignment(self, title, description, course_id, due_date, total_points=100.0):
        """创建新作业。
        
        Args:
            title (str): 作业标题
            description (str): 作业描述
            course_id (int): 课程ID
            due_date (datetime): 截止日期
            total_points (float): 总分，默认为100
            
        Returns:
            Assignment: 创建的作业对象
        """
        course = Course.get_by_id(course_id)
        return Assignment.create(
            title=title,
            description=description,
            course=course,
            due_date=due_date,
            total_points=total_points
        )
    
    def assign_to_students(self, assignment_id):
        """将作业分配给所有选课学生。
        
        Args:
            assignment_id (int): 作业ID
            
        Returns:
            int: 分配的学生作业数量
        """
        assignment = Assignment.get_by_id(assignment_id)
        students = StudentCourse.select().where(StudentCourse.course == assignment.course)
        
        # 批量创建学生作业记录
        created = 0
        for student_course in students:
            if not StudentAssignment.select().where(
                (StudentAssignment.student == student_course.student) &
                (StudentAssignment.assignment == assignment)
            ).exists():
                StudentAssignment.create(
                    student=student_course.student,
                    assignment=assignment
                )
                created += 1
        
        return created
    
    def submit_assignment(self, student_id, assignment_id, score=None):
        """提交或评分作业。
        
        Args:
            student_id (int): 学生用户ID
            assignment_id (int): 作业ID
            score (float, optional): 分数，如果提供则表示评分
            
        Returns:
            StudentAssignment: 更新后的学生作业对象
            
        Raises:
            ValueError: 如果找不到对应的学生作业记录
        """
        student_assignment = StudentAssignment.get_or_none(
            StudentAssignment.student_id == student_id,
            StudentAssignment.assignment_id == assignment_id
        )
        
        if not student_assignment:
            raise ValueError("无法找到对应的学生作业记录")
        
        student_assignment.submitted_at = datetime.now()
        student_assignment.attempts += 1
        
        if score is not None:
            student_assignment.score = score
            student_assignment.completed = True
            
        student_assignment.save()
        return student_assignment
    
    def get_student_assignments(self, student_id, course_id=None, completed=None):
        """获取学生的作业列表。
        
        Args:
            student_id (int): 学生用户ID
            course_id (int, optional): 课程ID，用于筛选指定课程的作业
            completed (bool, optional): 是否已完成，用于筛选作业状态
            
        Returns:
            list: 学生作业对象列表
        """
        query = StudentAssignment.select().where(StudentAssignment.student_id == student_id)
        
        if course_id:
            query = query.join(Assignment).where(Assignment.course_id == course_id)
            
        if completed is not None:
            query = query.where(StudentAssignment.completed == completed)
            
        return list(query)
    
    def get_course_assignments(self, course_id):
        """获取课程的所有作业。
        
        Args:
            course_id (int): 课程ID
            
        Returns:
            list: 作业对象列表
        """
        return list(Assignment.select().where(Assignment.course_id == course_id))
