from src.tools.calendar.check_availability_tool import CheckCalendarAvailability
from src.tools.calendar.create_event_tool import CreateCalendarEvent
from src.tools.calendar.delete_event_tool import DeleteCalendarEvent
from src.tools.calendar.find_timeslot_tool import FindCalendarTimeSlot
from src.tools.calendar.get_calendar_events_tool import GetCalendarEvents
from src.tools.calendar.update_event_tool import UpdateCalendarEvent
from src.tools.flights.flight_search_tool import FlightSearchTool
from src.tools.gmail.gmail_draft_tool import GmailDraftTool
from src.tools.gmail.gmail_manage_tool import GmailManageTool
from src.tools.gmail.gmail_search_tool import GmailSearchTool
from src.tools.jobs.cancel_job_tool import CancelJobTool
from src.tools.jobs.list_jobs_tool import ListJobsTool
from src.tools.jobs.schedule_job_tool import ScheduleJobTool
from src.tools.jobs.update_job_tool import UpdateJobTool
from src.tools.news.espn_tool import ESPNTool
from src.tools.news.hackernews_tool import HackerNewsTool
from src.tools.news.newsapi_tool import NewsAPITool
from src.tools.squash.squash_availability_tool import SquashCourtChecker
from src.tools.squash.squash_booking_tool import SquashBookingTool
from src.tools.system.update_timezone_tool import UpdateTimezoneTool
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
register(UpdateCalendarEvent())
register(DeleteCalendarEvent())
register(GetCalendarEvents())
register(FindCalendarTimeSlot())
register(CheckCalendarAvailability())
register(SquashCourtChecker())
register(SquashBookingTool())
register(FlightSearchTool())
register(NewsAPITool())
register(HackerNewsTool())
register(ESPNTool())
register(GmailSearchTool())
register(GmailDraftTool())
register(GmailManageTool())
register(ListTasksTool())
register(CreateTaskTool())
register(UpdateTaskTool())
register(CompleteTaskTool())
register(ScheduleJobTool())
register(ListJobsTool())
register(CancelJobTool())
register(UpdateJobTool())
register(UpdateTimezoneTool())
