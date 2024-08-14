from general_gui import GUIModelingBlock
from circle_indicator_gui import GUICircleIndicator
from options import OptionsCalculationInput
from helper_functions_general import delete_all
from config import *

class GUIConfigurationInput(GUIModelingBlock):
    """
    Manages a GUI configuration input block that decides the mathematical operation between connected attributes
    """
    def __init__(self, model, view, x, y):
        super().__init__(model, view, "?", x, y, INPUT_WIDTH, INPUT_HEIGHT, INPUT_COLOR, bind_left=MOUSE_DRAG, bind_right=MOUSE_PRESS, tags_rect=(TAG_INPUT,), tags_text=(TAG_INPUT_TEXT,))
        self.__attached_configuration_attribute_gui = None # The attribute it is connectde to
        self.__connections = []
        self.__symbol_calculation_type = None # Symbol representing the mathematical operation of this block
        self.__input_scalar_indicator = None
        self.__direction_out_from_block = None
        
    def left_pressed(self, event):
        # Move block if no connection was held and added
        if not self.attach_held_connection():
            super().left_pressed(event)
            
    def left_dragged(self, event):
        super().left_dragged(event)
        self.attempt_to_detach_from_attribute()
        
    def left_released(self, event):
        if super().left_released(event, False):
            self.attempt_to_attach_to_attribute()
            self.get_view().update_shown_order()
            
    def right_pressed(self, event):
        self.attach_held_connection()
        
    def open_options(self):
        return OptionsCalculationInput(self.get_model().get_root(), self)
        
    def attach_held_connection(self):
        """
        Attaches any held connection to this block
        
        Returns whether a connection was held
        """
        held_connection = self.get_view().get_held_connection()
        
        if held_connection != None:
            direction = "LEFT"
            
            if self.is_attached() and self.__attached_configuration_attribute_gui.get_x() < self.get_x():
                direction = "RIGHT"
                
            held_connection.set_end_location(self, direction)
            
            self.get_view().reset_held_connection()
            
            return True
            
        return False
        
    def move_block(self, move_x, move_y):
        super().move_block(move_x, move_y)
        
        # If panning or zooming, only the corresponding attribute should move the lines
        if not self.get_view().is_panning() and not self.get_view().is_zooming():
            for connection in self.__connections:
                connection.move_lines(move_x, move_y)
                
        if self.__input_scalar_indicator != None:
            self.__input_scalar_indicator.move(move_x, move_y)
            
    def scale(self, last_length_unit):
        super().scale(last_length_unit)
        
        if self.__input_scalar_indicator != None:
            self.__input_scalar_indicator.scale(last_length_unit)
            
    def attempt_to_attach_to_attribute(self):
        """
        Attempt to attach to an adjacent GUI configuration attribute
        """
        # Search all GUI configuration classes
        for configuration_class_gui in self.get_view().get_configuration_classes_gui():
            # Search all GUI configuration attributes per class
            for configuration_attribute_gui in configuration_class_gui.get_configuration_attributes_gui():
                # Check if adjacent
                is_adjacent, direction_out_of_block = configuration_attribute_gui.is_adjacent([(self.get_x(), self.get_y())])
                
                if is_adjacent and not configuration_attribute_gui.has_configuration_input():
                    self.__attached_configuration_attribute_gui = configuration_attribute_gui
                    self.__attached_configuration_attribute_gui.set_configuration_input(self)
                    
                    self.__direction_out_from_block = direction_out_of_block
                    
                    # Update calculation type of input block but not the attribute
                    if self.__attached_configuration_attribute_gui.get_configuration_class_gui().is_linked() and self.__attached_configuration_attribute_gui.get_configuration_attribute().get_symbol_calculation_type() != None:
                        self.update_symbol_calculation_type()
                        
                    # Updated calculation type of attribute according to the input block
                    else:
                        self.__attached_configuration_attribute_gui.set_calculation_type(self.__symbol_calculation_type)
                        
                    for connection in self.__connections:
                        self.attempt_to_add_connection_to_attribute(connection)
                        
                        # If changing side of input block, the connections should also change side
                        connection.update_direction(self, self.__direction_out_from_block)
                        
                    self.__attached_configuration_attribute_gui.update_value_input_type_setup_attributes_gui()
                    self.update_input_scalar()
                    break
                    
    def attempt_to_detach_from_attribute(self):
        """
        Detach from an adjacent attribute if this block was previously attached
        """
        # Remove from being an input to an attribute
        if self.is_attached():
            self.__attached_configuration_attribute_gui.remove_configuration_input()
            
            # Find if this was the only linked copy that had an input block
            linked_configuration_attributes_with_input = 0
            
            for linked_configuration_attribute_gui in self.get_model().get_linked_configuration_attributes_gui(self.__attached_configuration_attribute_gui):
                if linked_configuration_attribute_gui.has_configuration_input():
                    linked_configuration_attributes_with_input += 1
                    
            # Reset calculation type and input scalar if this was the only linked copy that had an input block
            if linked_configuration_attributes_with_input == 0:
                self.__attached_configuration_attribute_gui.reset_calculation_type()
                self.__attached_configuration_attribute_gui.reset_input_scalar()
                
            for connection in self.__connections:
                input_configuration_attribute = connection.get_start_block().get_configuration_attribute()
                self.__attached_configuration_attribute_gui.get_configuration_attribute().remove_input_configuration_attribute(input_configuration_attribute)
                
            self.__attached_configuration_attribute_gui.update_value_input_type_setup_attributes_gui()
            self.__attached_configuration_attribute_gui = None
            self.__direction_out_from_block = None
            
            self.update_input_scalar(move_back_input=False)
            
    def is_attached(self):
        """
        Returns whether this block is attached to a configuration attribute
        """
        return self.__attached_configuration_attribute_gui != None
        
    def get_attached_configuration_attribute_gui(self):
        """
        Returns the configuration attribute this block is attached to
        """
        return self.__attached_configuration_attribute_gui
        
    def get_symbol_calculation_type(self):
        """
        Returns the mathematical operation of this input block
        """
        return self.__symbol_calculation_type
        
    def set_symbol_calculation_type(self, symbol_calculation_type):
        """
        Sets the mathematical operation of this input block
        """
        self.__symbol_calculation_type = symbol_calculation_type
        self.set_text(symbol_calculation_type)
        
        if self.is_attached():
            self.__attached_configuration_attribute_gui.set_calculation_type(symbol_calculation_type)
            
        self.update_connection_numbers()
        
    def update_symbol_calculation_type(self):
        """
        Update the employed mathematical operation based on the configured operation for the connected configuration attribute
        """
        if self.is_attached():
            self.__symbol_calculation_type = self.__attached_configuration_attribute_gui.get_configuration_attribute().get_symbol_calculation_type()
            text = self.__symbol_calculation_type
            
            if text == None:
                text = "?"
                
            self.set_text(text)
            
    def set_input_scalar(self, input_scalar):
        """
        Sets a float scalar that scales the final output value from the mathematical operation between input values before being added to the setup version of this attribute
        """
        if self.is_attached():
            self.__attached_configuration_attribute_gui.set_input_scalar(float(input_scalar))
            
            self.update_input_scalar()
            
    def update_input_scalar(self, *, move_back_input=True, update_linked=True):
        """
        Updates the shown scalar that scales the final output value from the mathematical operation between input values
        """
        # Remove any existing indicator
        if self.__input_scalar_indicator != None:
            self.__input_scalar_indicator.remove()
            
            # Move the input block back to be adjacent with the attribute
            if move_back_input:
                self.move_block(self.__input_scalar_indicator.get_x()-self.get_x()-0.5, 0)
                
        if self.is_attached():
            input_scalar = self.__attached_configuration_attribute_gui.get_input_scalar()
            
            # If the indicator should be shown
            if input_scalar not in (None, DEFAULT_INPUT_SCALAR):
                indicator_x = self.get_x() + 0.5
                self.move_block(self.get_move_x_due_to_indicator(), 0)
                
                self.__input_scalar_indicator = GUICircleIndicator(self.get_view(), indicator_x, self.get_y()+0.5, INPUT_SCALAR_CIRCLE_RADIUS, INPUT_SCALAR_CIRCLE_COLOR, INPUT_SCALAR_CIRCLE_OUTLINE, input_scalar)
                
            # Update linked copies of the attribute that this input block is attached to
            if update_linked:
                for linked_configuration_attribute_gui in self.get_model().get_linked_configuration_attributes_gui(self.__attached_configuration_attribute_gui):
                    if linked_configuration_attribute_gui.has_configuration_input():
                        linked_configuration_attribute_gui.get_configuration_input().update_input_scalar(update_linked=False)
                        
    def get_move_x_due_to_indicator(self):
        """
        Returns the distance in x of the grid that the input block should move to make room for the indicator for the input scalar
        """
        if self.__direction_out_from_block == "LEFT":
            return -1
            
        elif self.__direction_out_from_block == "RIGHT":
            return 1
            
    def attempt_to_add_connection_to_attribute(self, connection):
        """
        Attempts to connect the attribute that a connection starts from with the attribute that this input block is connected to (the calculation versions of the blocks without any GUI do not have any designated input blocks)
        """
        if self.is_attached():
            is_internal = self.__attached_configuration_attribute_gui.get_configuration_class_gui() == connection.get_start_block().get_configuration_class_gui() and not connection.is_external()
            connected_configuration_attribute = connection.get_start_block().get_configuration_attribute()
            
            self.__attached_configuration_attribute_gui.get_configuration_attribute().add_input_configuration_attribute(connected_configuration_attribute, is_internal)
            
    def add_connection(self, connection):
        """
        Add a connection to track as being connected to this input block
        """
        self.__connections.append(connection)
        self.attempt_to_add_connection_to_attribute(connection)
        
        self.update_connection_numbers()
            
    def remove_connection(self, connection):
        """
        Remove a connection from being tracked as connected to this input block
        """
        self.__connections.remove(connection)
        
        # Remove from the calculation version of the attribute block without GUI if attached to an attribute
        if self.is_attached():
            configuration_attribute_to_disconnect = connection.get_start_block().get_configuration_attribute()
            self.__attached_configuration_attribute_gui.get_configuration_attribute().remove_input_configuration_attribute(configuration_attribute_to_disconnect)
            
        self.update_connection_numbers()
        
    def update_connection_numbers(self):
        """
        Updates the number showning the order which inputs are considered, if applicable
        """
        for i, connection in enumerate(self.__connections):
            # The mathematical operation is dependent on the order of the inputs
            if self.__symbol_calculation_type in ENUMERATED_INPUT_CALCULATION_TYPE_SYMBOLS:
                connection.set_num_order(i+1)
            else:
                connection.set_num_order(None)
                
    def delete(self):
        super().delete()
        self.attempt_to_detach_from_attribute()
                
        delete_all(self.__connections)
        self.get_view().remove_configuration_input_gui(self)
        
        if self.__input_scalar_indicator != None:
            self.__input_scalar_indicator.remove()
            
    def save_state(self):
        saved_states = super().save_state() | {"symbol_calculation_type": self.get_symbol_calculation_type(), "connections": [connection.save_state() for connection in self.__connections]}
        
        if self.is_attached() and self.__attached_configuration_attribute_gui.get_input_scalar() not in (None, DEFAULT_INPUT_SCALAR):
            saved_states["x"] -= self.get_move_x_due_to_indicator()
            
        return saved_states
