from src.tools.calendar.check_availability_tool import CheckCalendarAvailability
from src.tools.calendar.create_event_tool import CreateCalendarEvent
from src.tools.calendar.find_timeslot_tool import FindCalendarTimeSlot
from src.tools.calendar.get_calendar_events_tool import GetCalendarEvents
from src.tools.squash.squash_availability_tool import SquashCourtChecker
from src.tools.squash.squash_booking_tool import SquashBookingTool
from src.tools.tasks.complete_task import CompleteTaskTool
from src.tools.tasks.create_task_tool import CreateTaskTool
from src.tools.tasks.list_tasks_tool import ListTasksTool
from src.tools.tasks.update_task_tool import UpdateTaskTool
from src.tools.tennis.confirm_tennis_court_reservation_tool import TennisCourtConfirmTool
from src.tools.tennis.start_tennis_court_reservation_tool import TennisCourtBookerInitialization
from src.tools.tennis.tennis_schedule_tool import TennisScheduleChecker

TOOLS = {}


def register(tool_instance):
    TOOLS[tool_instance.name] = tool_instance


def get_tool(name):
    return TOOLS.get(name)


register(TennisScheduleChecker())
register(TennisCourtBookerInitialization())
register(TennisCourtConfirmTool())
register(CreateCalendarEvent())
register(GetCalendarEvents())
register(FindCalendarTimeSlot())
register(CheckCalendarAvailability())
register(SquashCourtChecker())
register(SquashBookingTool())
register(ListTasksTool())
register(CreateTaskTool())
register(UpdateTaskTool())
register(CompleteTaskTool())
