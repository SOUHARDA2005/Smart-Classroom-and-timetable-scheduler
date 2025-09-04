import pandas as pd
#Sample Data
classes= pd.DataFrame({
    'class_id': [1,2,3],
    'class_name':['math','science','english'],
    'teacher_id':[1,2,3],
    'students':[['A','B'],['A','C'],['B','C']]

})

teachers = pd.DataFrame({
    'teacher_id':[1,2,3],
    'teacher_name':['Mr.Roy','Mr.Sen','Mrs.Naskar']
})

rooms = pd.DataFrame({
    'room_id':[101,102],
    'room_name':['Room A','Room B']
})

timeslots= pd.DataFrame({
    'timeslot_id':[1,2,3],
    'timeslot_name':['9-10AM','10-11Am','11-12PM']
})

from ortools.sat.python import cp_model

def create_timetable(classes,teachers,rooms,timeslots):
    model=cp_model.CpModel()
    #Variables
    timetable={}
    for class_id in classes['class_id']:
        for room_id in rooms['room_id']:
            for timeslot_id in timeslots['timeslot_id']:
                timetable[(class_id,room_id,timeslot_id)]= model.NewBoolVar(f'class{class_id}_room{room_id}_timeslot{timeslot_id}')
    #Constraints
    #Each class must be assigned exactly one timeslot and one room
    for class_id in classes['class_id']:
        model.Add(sum(timetable[(class_id,room_id,timeslot_id)] for room_id in rooms['room_id'] for timeslot_id in timeslots['timeslot_id']) ==1)
    #No room can be assigned to more than one class at the same time
    for room_id in rooms['room_id']:
        for timeslot_id in timeslots['timeslot_id']:
         model.Add(sum(timetable[(class_id,room_id,timeslot_id)] for class_id in classes['class_id'])<=1)
    #No teacher can be in two places at the same time
    for teacher_id in teachers['teacher_id']:
        class_ids=classes[classes['teacher_id'] == teacher_id] ['class_id']
        for timeslot_id in timeslots['timeslot_id']:
             model.Add(sum(timetable[(class_id,room_id,timeslot_id)] for class_id in class_ids for room_id in rooms['room_id'])<=1)
    #Solver
    solver= cp_model.CpSolver()
    status= solver.Solve(model)

    if status in (cp_model.FEASIBLE, cp_model.OPTIMAL) :
        for class_id in classes['class_id']:
            for room_id in rooms['room_id']:
                for timeslot_id in timeslots['timeslot_id']:
                    if solver.Value(timetable[(class_id,room_id,timeslot_id)])==1:
                        print(f'class {class_id} is scheduled in room {room_id} at Timeslot {timeslot_id}')
    else:
        print("No feasible solution found.")
create_timetable(classes,teachers,rooms,timeslots)



