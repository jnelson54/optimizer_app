import streamlit as st
import pulp

st.title("Task Allocation & Staffing Optimizer")

st.write("Enter up to 10 tasks. For each task, provide a name and the required hours.")

num_tasks = 10
tasks = {}
cols = st.columns(2)
for i in range(num_tasks):
    task_name = cols[0].text_input(f"Task {i+1} Name:", value=f"Task_{i+1}")
    required_hours = cols[1].number_input(f"Hours for {task_name}:", min_value=0.0, step=0.5, value=0.0)
    if task_name.strip() != "" and required_hours > 0:
        tasks[task_name] = required_hours

st.write("---")

total_hours_per_shift = st.number_input("Hours per shift:", min_value=1.0, value=8.0)
shifts_per_day = st.number_input("Number of shifts per day:", min_value=1, value=1)
daily_total_available = st.number_input("Total available worker-hours per day (e.g. 30):", min_value=1.0, value=30.0)
buffer = st.number_input("Buffer fraction (e.g. 0.2 for 20%):", min_value=0.0, value=0.2)
downtime = st.number_input("Downtime fraction (e.g. 0.2 for 20% downtime):", min_value=0.0, max_value=1.0, value=0.2)

# Additional assumptions for scaling up staffing needs
days_per_week = st.number_input("Working days per week:", min_value=1, value=5)
days_per_month = st.number_input("Working days per month:", min_value=1, value=22)
days_per_year = st.number_input("Working days per year:", min_value=1, value=260)

if st.button("Optimize"):
    if not tasks:
        st.warning("Please enter at least one task with required hours.")
    else:
        # Linear Programming Model
        prob = pulp.LpProblem("Task_Allocation", pulp.LpMinimize)

        # Variables: hours assigned to each task
        x = {t: pulp.LpVariable(t, lowBound=0) for t in tasks}

        # Objective: minimize total assigned hours (just a placeholder objective)
        prob += pulp.lpSum([x[t] for t in tasks]), "Minimize_Total_Hours"

        # Constraints:
        # Each task must get at least its required hours * (1+buffer)
        for t, hrs in tasks.items():
            prob += x[t] >= hrs * (1 + buffer), f"MinRequirement_{t}"

        # Total hours cannot exceed daily available hours
        prob += pulp.lpSum([x[t] for t in tasks]) <= daily_total_available, "DailyCapacity"

        # Solve the LP
        prob.solve(pulp.PULP_CBC_CMD(msg=0))

        if pulp.LpStatus[prob.status] != "Optimal":
            st.error("No optimal solution found. Try adjusting constraints.")
        else:
            allocated_hours = {t: x[t].varValue for t in tasks}
            total_assigned = sum(allocated_hours.values())

            st.subheader("Optimal Allocation of Hours per Day:")
            for t, val in allocated_hours.items():
                st.write(f"{t}: {val:.2f} hours")

            st.write(f"**Total Hours Allocated (Day):** {total_assigned:.2f}")

            # Calculate effective working hours per person considering downtime
            effective_hours_per_person_per_day = total_hours_per_shift * shifts_per_day * (1 - downtime)

            # Number of people needed per day
            if effective_hours_per_person_per_day > 0:
                people_per_day = total_assigned / effective_hours_per_person_per_day
            else:
                people_per_day = float('inf')

            st.subheader("Staffing Requirements:")
            st.write(f"Effective Working Hours/Person/Day: {effective_hours_per_person_per_day:.2f}")

            st.write(f"People Required Per Day: {people_per_day:.2f}")
            st.write(f"People Required Per Week (approx): {people_per_day * days_per_week:.2f}")
            st.write(f"People Required Per Month (approx): {people_per_day * days_per_month:.2f}")
            st.write(f"People Required Per Year (approx): {people_per_day * days_per_year:.2f}")
