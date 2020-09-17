from kivy.app import App
from kivy.lang import Builder
from kivy.uix.recycleview import RecycleView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from database_manager import DatabaseManager
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.recycleview import RecycleView, RecycleViewBehavior
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.treeview import TreeView, TreeViewLabel, TreeViewNode
from kivy.uix.widget import Widget
from kivy.uix.behaviors import FocusBehavior
from kivy.uix.recycleview.layout import LayoutSelectionBehavior
from kivy.properties import NumericProperty, StringProperty, ObjectProperty, BooleanProperty
from kivy.uix.checkbox import CheckBox
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivycalendar import DatePicker
from kivy.clock import Clock
import re
from kivy.uix.textinput import TextInput


database_manager = DatabaseManager()
items = database_manager.transaction_get_all()



class MainWindow(Screen):
    pass

class WindowManager(ScreenManager):
    pass

##TransactionTreeView Group

#Custom node to display transaction
class TransactionTreeNode(GridLayout, TreeViewNode):
    transac_id = NumericProperty()
    transac_amount_int = NumericProperty()
    transac_amount = StringProperty()
    transac_details = StringProperty()
    transac_notes = StringProperty()
    transac_dates = StringProperty()
    def __init__(self, transaction_list,details_list,**kwargs):
         
        self.transac_id = transaction_list[0]
        self.transac_dates = transaction_list[1]
        self.transac_amount_int = transaction_list[2]
        self.transac_amount = str(transaction_list[2])
        if transaction_list[3] is None:
            self.transac_details = details_list[0]
        else:
            self.transac_details= details_list[transaction_list[3]]
        self.transac_notes = (transaction_list[4])
        super(TransactionTreeNode, self).__init__(**kwargs)
    
    def get_id(self):
        if self.transac_amount_int > 0:
            transac_type = 1
        elif self.transac_amount_int < 0:
            transac_type = 0
        return [self.transac_id, transac_type,self.transac_dates, self.transac_amount, self.transac_details, self.transac_notes]
        

class TransactionTreeView(TreeView):
    
    def __init__(self,**kwargs):
        super(TransactionTreeView,self).__init__(**kwargs)
    
    def select_node(self,node):
        if not node.is_selected:
            super(TransactionTreeView,self).select_node(node)
            if isinstance(self.selected_node, TransactionTreeNode):
                self.parent.node_is_selected = True
            else:
                self.parent.node_is_selected = False
        else:
            self.deselect_node(node)
            self.parent.node_is_selected = False
        
        
    
    def on_selected_node(self,instance,value):
        if isinstance(self.selected_node, TransactionTreeNode):
            self.parent.selected_node = self.selected_node
    


#Custom tree to display transaction
class ScrollableTransactionTreeView(ScrollView):
    selected_node = ObjectProperty(None)
    node_is_selected = BooleanProperty(None)
    def populate_tree_view(self, tree_view, details_list, parent, node):
        if parent is None:
            tree_node = tree_view.add_node(TreeViewLabel(text=node['node_id'],
                                                        is_open=True))
        elif node['children'] == []:
            tree_node = tree_view.add_node(TransactionTreeNode(transaction_list = node['node_id'], details_list=details_list,is_open=True), parent)
        else:
            tree_node = tree_view.add_node(TreeViewLabel(text=node['node_id'],
                                                        is_open=True), parent)

        for child_node in node['children']:
            self.populate_tree_view(tree_view, details_list, tree_node, child_node)

    def convert_transaction_list_to_tree(self,items):
        tree = {'node_id': 'transaction',
        'children': []}

        dates = list(set(x[1] for x in items))

        dates.sort(reverse=True)
        
        def change(date,items):
            a = [item for item in items if item[1] == date]
            return a
        dictionary = ({date: change(date,items) for date in dates})

        for key in dictionary:
            transac_tree = {'node_id': key, 'children': []}
            for transaction in dictionary[key]:
                transac_tree['children'].append({'node_id': (transaction), 'children': []})

            tree['children'].append(transac_tree)
    
        return (tree)

    def __init__(self, **kwargs):
        super(ScrollableTransactionTreeView, self).__init__(**kwargs)
        tree = self.convert_transaction_list_to_tree(items)

        self.selected_node = ObjectProperty(None)
        self.node_is_selected = False
        self.tv = TransactionTreeView(root_options=dict(text='Tree One'),
                hide_root=True,
                indent_level=4)

        self.tv.size_hint = 1, None
        self.tv.bind(minimum_height = self.tv.setter('height'))
        self.details_list = self.generate_details_list()
        for child in tree['children']:
            self.populate_tree_view(self.tv, self.details_list, self.tv.root, child)
        
        self.add_widget(self.tv)
        Clock.schedule_once(self.after_init)

    def generate_details_list(self):
        items = database_manager.details_read_all()
        details_list = ['All']

        for item in items:
            details_list.append(item[1])

        return details_list

    def after_init(self, dt):
        self.app = App.get_running_app()
        self.app.scrollable = self

    def get_items(self):
        return database_manager.transaction_get_all()

    def refresh_tree(self):
        for node in [i for i in self.tv.iterate_all_nodes()]:
            self.tv.remove_node(node)
        
        print(App.get_running_app())
        items = self.get_items()
        tree = self.convert_transaction_list_to_tree(items)
        for child in tree['children']:
            self.populate_tree_view(self.tv, self.details_list, self.tv.root, child)
        
##Popups and their elements
#The Create Transaction Popup Screen
class CreateTransactionPopUp(Popup):
    obj_type = ObjectProperty(None)
    obj_amount = ObjectProperty(None)
    obj_date = ObjectProperty(None)
    earnings_or_spendings = StringProperty('earnings')
    obj_details = ObjectProperty(None)
    obj_notes = ObjectProperty(None)
    earnings_togglebutton = ObjectProperty(None)
    spendings_togglebutton =  ObjectProperty(None)
    def save(self):
        if self.earnings_or_spendings == "earnings":
            amount = float(self.obj_amount.text)
        else:
            amount = -float(self.obj_amount.text)
        if self.obj_details.details_id is not None:
            database_manager.transaction_create(date = self.obj_date.text, amount = amount, details_id = int(self.obj_details.details_id), notes = self.obj_notes.text )
        else:
            database_manager.transaction_create(date = self.obj_date.text, amount = float(self.obj_amount.text), notes = self.obj_notes.text )
        print('created transaction entry!')

    def set_transaction_type(self, transaction_type):
        if(transaction_type == 'earnings'):
            self.earnings_or_spendings = 'earnings'
        elif(transaction_type == 'spendings'):
            self.earnings_or_spendings = 'spendings'
    
    def show_details_viewer_popup(self):
        popupWindow = DetailsViewer(title = "Details Viewer", size_hint = (None, None), size=(500,300))
        popupWindow.open()

class TransactionDetailsDropDownButton(Button):
    def __init__(self, **kwargs):
        super(TransactionDetailsDropDownButton, self).__init__(**kwargs)
        self.text ='All'
        self.details_id = None
        self.dropdown = DropDown()
        self.dropdown.max_height = 150
        self.populate('earnings')
        self.bind(on_release=self.dropdown.open)
        self.dropdown.bind(on_select=lambda instance, x: setattr(self, 'text', x[1]))
        self.dropdown.bind(on_select= lambda instance,x: setattr(self,'details_id',x[0]))

    def reset_button(self):
        self.text = 'All'
        self.details_id = None

    def populate(self, earnings_or_spendings):
        self.dropdown.clear_widgets()

        transaction_details = []
        if earnings_or_spendings == "earnings":
            transaction_details = database_manager.details_read_by_type(1)
        elif earnings_or_spendings == "spendings":
            transaction_details = database_manager.details_read_by_type(0)
        
        btn = Button(text = 'All', size_hint_y = None, height =44)
        btn.data = (None,'All')
        btn.bind(on_release=lambda btn: self.dropdown.select(btn.data))

        # then add the button inside the dropdown
        self.dropdown.add_widget(btn)


        for transaction_detail in transaction_details:
            # When adding widgets, we need to specify the height manually
            # (disabling the size_hint_y) so the dropdown can calculate
            # the area it needs.

            btn = Button(text=transaction_detail[1] , size_hint_y=None, height=44)
            btn.data = (str(transaction_detail[0]),transaction_detail[1])
            
            # for each button, attach a callback that will call the select() method
            # on the dropdown. We'll pass the text of the button as the data of the
            # selection.
            btn.bind(on_release=lambda btn: self.dropdown.select(btn.data))

            # then add the button inside the dropdown
            self.dropdown.add_widget(btn)

class FloatInput(TextInput):
    pat = re.compile('[^0-9]')
    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        if '.' in self.text:
            s = re.sub(pat, '', substring)
        else:
            s = '.'.join([re.sub(pat, '', s) for s in substring.split('.', 1)])
        return super(FloatInput, self).insert_text(s, from_undo=from_undo)


            
#The Modify Transaction Popup Screen
class ModifyTransactionPopUp(CreateTransactionPopUp):
    transaction_on_edit = ObjectProperty(None)

    def __init__(self,selected_transaction ,**kwargs):
        self.transaction_on_edit = selected_transaction[0]

        super(ModifyTransactionPopUp,self).__init__(**kwargs)
        self.obj_amount.text =  selected_transaction[3]
        self.obj_date.text = selected_transaction[2]
        self.obj_details.text = selected_transaction[4]
        self.obj_details.details_id = selected_transaction[4]
        self.obj_notes.text = selected_transaction[5]
        self.obj_type = selected_transaction[1]

        if selected_transaction[1] == 0:
            transaction_type = 'spendings'
            self.earnings_togglebutton.state = 'normal'
            self.spendings_togglebutton.state = 'down'
        else:
            transaction_type = 'earnings'
            self.earnings_togglebutton.state = 'down'
            self.spendings_togglebutton.state = 'normal'

        self.obj_details.populate(transaction_type)
        self.set_transaction_type(transaction_type)

    def save(self):
        if self.earnings_or_spendings == "earnings":
            amount = float(self.obj_amount.text)
        else:
            amount = -float(self.obj_amount.text)
        database_manager.transaction_update(transaction_id = self.transaction_on_edit,date = self.obj_date.text, amount = float(self.obj_amount.text), details_id = int(self.obj_details.details_id), notes = self.obj_notes.text)
        print('modified transaction entry')
        
class DeleteTransactionPopUp(Popup):
    def __init__(self, selected_transaction, **kwargs):
        self.transaction_on_edit = selected_transaction[0]
        super(DeleteTransactionPopUp,self).__init__(**kwargs)
    
    def save(self):
        database_manager.transaction_delete(self.transaction_on_edit)
        print('deleted transaction entry')


##DETAILS POPUP
class SelectableRecycleBoxLayout(FocusBehavior, LayoutSelectionBehavior,
                                 RecycleBoxLayout):
    touch_deselect_last = BooleanProperty(True)


class DetailsViewerViewclass(RecycleDataViewBehavior, BoxLayout):
    index = None
    selected = BooleanProperty(False)
    selectable = BooleanProperty(True)
    cols = 3
    label1_text = ObjectProperty(None)
    selected_index = None


    def refresh_view_attrs(self, rv, index, data):
        ''' Catch and handle the view changes '''
        self.index = index
        self.label1_text = data['text']
        self.details_id = str(data['details_id'])
        self.parent_populate = data['populate_rv']
        self.det_type = data['det_type']

        return super(DetailsViewerViewclass, self).refresh_view_attrs(
             rv, index, data)

    def on_touch_down(self, touch):
        ''' Add selection on touch down '''
        if super(DetailsViewerViewclass, self).on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos) and self.selectable:
            return self.parent.select_with_touch(self.index, touch)

    def apply_selection(self, rv, index, is_selected):
        ''' Respond to the selection of items in the view. '''
        self.selected = is_selected
        
    
    def refresh_parent(self,value):
        self.parent_populate()

    def delete_popup(self,rv,index,is_selected):
        popup = DeleteDetailsPopup(self.details_id, title = "Delete Details", size_hint = (None, None), size=(300,250))
        popup.bind(on_dismiss=self.refresh_parent)
        popup.open()
    
    def modify_popup(self,rv,index,is_selected):
        popup = ModifyDetailsPopup([self.details_id,self.label1_text,self.det_type], title = "Modify Details", size_hint = (None, None), size=(300,250))
        popup.bind(on_dismiss = self.refresh_parent)
        popup.open()

class CreateDetailsPopup(Popup):
    earnings_or_spendings = StringProperty(None)
    earnings_or_spendings = 'earnings'
    details_name = ObjectProperty(None)
    earnings_togglebutton = ObjectProperty(None)
    spendings_togglebutton =  ObjectProperty(None)

    def set_earnings_or_spendings(self,earnings_or_spendings):

        if earnings_or_spendings == 'earnings':
            self.earnings_or_spendings = 'earnings'
        elif earnings_or_spendings == 'spendings':
            self.earnings_or_spendings = 'spendings'
            
    def save(self, database_manager = database_manager):
        if self.earnings_or_spendings == "earnings":
            det_type = 1
        if self.earnings_or_spendings == "spendings":
            det_type = 0
        database_manager.details_create(name = self.details_name.text, transaction_type = det_type)
        print("created new detail!")

class ModifyDetailsPopup(CreateDetailsPopup):
    def __init__(self, selected_details, **kwargs):
        super(ModifyDetailsPopup,self).__init__(**kwargs)
        self.index =  selected_details[0]
        self.details_name.text = selected_details[1]
        if selected_details[2] == 0:
            self.set_earnings_or_spendings('spendings')
            self.earnings_togglebutton.state = 'normal'
            self.spendings_togglebutton.state = 'down'
        else:
            self.set_earnings_or_spendings('earnings')
            self.earnings_togglebutton.state = 'down'
            self.spendings_togglebutton.state = 'normal'
    
    def save(self, database_manager = database_manager):
        if self.earnings_or_spendings == "earnings":
            det_type = 1
        if self.earnings_or_spendings == "spendings":
            det_type = 0
        
        print(self.index,self.details_name.text,det_type)
        database_manager.details_update(self.index,self.details_name.text,det_type)
        print('updated a detail!')


class DeleteDetailsPopup(Popup):
    def __init__(self, selected_detail, **kwargs):
        self.selected_detail = selected_detail
        super(DeleteDetailsPopup,self).__init__(**kwargs)
    
    def save(self):
        database_manager.details_delete(self.selected_detail)
        print('deleted detail entry')

class DetailsViewer(Popup):
    earnings_or_spendings = 'earnings'

    def __init__(self,**kwargs):
        self.detailsviewerlist = ObjectProperty(None)
        super(DetailsViewer,self).__init__(**kwargs)
        print(self.detailsviewerlist)

    def set_earnings_or_spendings(self,earnings_or_spendings):
        if earnings_or_spendings =='earnings':
            self.earnings_or_spendings = 'earnings'
        elif earnings_or_spendings =='spendings':
            self.earnings_or_spendings = 'spendings'

    def refresh(self,value):
        self.detailsviewerlist.populate()

    def show_create_details_popup(self):
        popupWindow = CreateDetailsPopup(title = "Create Details", size_hint = (None, None), size=(300,250))
        
        popupWindow.bind(on_dismiss = self.refresh)
        popupWindow.open()

class DetailsViewerList(RecycleView):
    def __init__(self, details_database = database_manager,**kwargs):
        super(DetailsViewerList, self).__init__(**kwargs)
        self.earnings_or_spendings  = 'earnings'
        self.populate(details_database)
    
    def set_earnings_or_spendings(self,earnings_or_spendings):
        if earnings_or_spendings =='earnings':
            self.earnings_or_spendings = 'earnings'
        elif earnings_or_spendings =='spendings':
            self.earnings_or_spendings = 'spendings'

    def populate(self, details_database = database_manager):
        if self.earnings_or_spendings == 'earnings':
            datas = details_database.details_read_by_type(1)
            det_type = 1
        else:
            datas = details_database.details_read_by_type(0)
            det_type = 0
        self.data = []

        for data in datas:
            self.data.append({'text': data[1], 'details_id': data[0], 'populate_rv': self.populate, 'det_type': det_type})
        


#Implements the whole Transaction Viewer
class TransactionViewerWidget(BoxLayout):

    def __init__(self, **kwargs):

        super(TransactionViewerWidget,self).__init__(**kwargs)

        
    def show_create_transaction_popup(self):

        popupWindow = CreateTransactionPopUp(title="Create Transaction", size_hint=(None,None),size=(400,400)) 
        # Create the popup window

        popupWindow.open()

    def show_modify_transaction_popup(self, selected_transaction):
        popupWindow = ModifyTransactionPopUp(title="Modify Transaction", selected_transaction = selected_transaction, size_hint =(None,None), size=(400,400))
        popupWindow.open()    

    def show_delete_transaction_popup(self, selected_transaction):
        popupWindow = DeleteTransactionPopUp(title = "Delete Transaction", selected_transaction = selected_transaction, size_hint = (None, None), size=(400,400))
        popupWindow.open()
    


kv = Builder.load_file("transactiontracker.kv")

class TestApp(App):
    
    scrollable = None
    def build(self):
        return kv


if __name__ == '__main__':
    TestApp().run()